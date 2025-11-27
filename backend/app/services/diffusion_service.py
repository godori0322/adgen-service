# diffusion_service.py
#
# SD1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)
# - bitsandbytes / Quantization 전부 제거
# - 모든 서브모델(CN, UNet, VAE, TextEncoder)을 같은 device로 강제 정렬
# - L4 24GB 기준 fp16 사용 (CUDA), CPU면 fp32

from dotenv import load_dotenv
load_dotenv()

import os
import torch
from PIL import Image, ImageDraw, ImageFont
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
)
from controlnet_aux import MidasDetector
import numpy as np
from io import BytesIO
from typing import Optional
import random

# -----------------------------------------------------------------------------#
# 캐시 / 경로 설정                                                              #
# -----------------------------------------------------------------------------#

# main.py에서 이미 설정했지만, 단독 실행/테스트를 대비해 한 번 더 명시
os.environ.setdefault("HF_HOME", "/home/shared/models")
os.environ.setdefault("DIFFUSERS_CACHE", "/home/shared/models")
os.environ.setdefault("TRANSFORMERS_CACHE", "/home/shared/models")
os.environ.setdefault("TORCH_HOME", "/home/shared/models")
os.environ.setdefault("SAM_MODEL_PATH", "/home/shared/models/sam_vit_h_4b8939.pth")

HF_CACHE_DIR = "/home/shared/models"  # 공용 캐시/모델 디렉터리 경로 상수

# -----------------------------------------------------------------------------#
# 설정: SD 1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)                          #
# -----------------------------------------------------------------------------#

SD15_MODEL_ID = "runwayml/stable-diffusion-v1-5"
CONTROLNET_DEPTH_ID = "lllyasviel/control_v11f1p_sd15_depth"
IP_ADAPTER_MODEL_ID = "h94/IP-Adapter"
IP_ADAPTER_SUBFOLDER = "models"
IP_ADAPTER_WEIGHT_NAME = "ip-adapter_sd15.bin"  # SD1.5용 IP-Adapter 가중치 파일명

# 전역 캐시
_pipeline = None
_midas_detector = None
_ip_adapter_loaded = False


# -----------------------------------------------------------------------------#
# 파이프라인 로딩 함수                                                          #
# -----------------------------------------------------------------------------#

def _load_pipeline():
    """
    SD 1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)를 모두 로드하고
    전역 변수에 캐싱하는 함수
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded

    if _pipeline is not None:
        return _pipeline

    print("[SD15 Pipeline] Loading base models...")

    # 디바이스 / dtype 설정
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if device == "cuda" else torch.float32

    # 1) ControlNet(Depth) 로드
    controlnet_depth = ControlNetModel.from_pretrained(
        CONTROLNET_DEPTH_ID,
        cache_dir=HF_CACHE_DIR,
        torch_dtype=torch_dtype,
    ).to(device)

    # 2) StableDiffusionControlNetPipeline 로드 (Base: SD 1.5)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        SD15_MODEL_ID,
        controlnet=controlnet_depth,
        cache_dir=HF_CACHE_DIR,
        torch_dtype=torch_dtype,
        safety_checker=None,         # 광고용이라면 별도 필터링에서 처리
        use_safetensors=True,
    ).to(device)

    print(f"[SD15 Pipeline] 기본 fp16/fp32로 로드했습니다. device={device}, dtype={torch_dtype}")

    # 3) 스케줄러/메모리 최적화
    try:
        if device == "cuda":
            pipe.enable_xformers_memory_efficient_attention()
            print("[SD15 Pipeline] xformers 활성화됨.")
    except Exception as e:
        print(f"[WARNING] xformers 활성화 실패: {e}")

    pipe.enable_vae_slicing()
    try:
        pipe.enable_vae_tiling()
    except Exception:
        pass

    # 4) Depth 전처리기(Midas) 로드
    print("[Midas Detector] Depth 전처리기 로드 중...")
    _midas_detector = MidasDetector.from_pretrained(
        "lllyasviel/ControlNet",
        cache_dir=HF_CACHE_DIR,
    ).to(device)
    print("[Midas Detector] Depth 전처리기 성공적으로 로드됨.")

    # 5) IP-Adapter(SD1.5) 로드
    global _ip_adapter_loaded
    print("[IP-Adapter] SD1.5용 IP-Adapter 로드 중...")
    try:
        pipe.load_ip_adapter(
            IP_ADAPTER_MODEL_ID,          # "h94/IP-Adapter"
            subfolder=IP_ADAPTER_SUBFOLDER,
            weight_name=IP_ADAPTER_WEIGHT_NAME,
        )
        pipe.set_ip_adapter_scale(0.0)    # 기본값은 비활성화
        _ip_adapter_loaded = True
        print(
            f"[IP-Adapter] {IP_ADAPTER_SUBFOLDER}/{IP_ADAPTER_WEIGHT_NAME} 로드 성공."
        )
    except Exception as e:
        print(f"[WARNING] IP-Adapter 로드 실패: {e}. 우선 ControlNet만 사용함.")
        _ip_adapter_loaded = False

    # 6) 모든 서브모델 동일 디바이스로 강제 정렬 (CPU/CUDA 혼합 방지 핵심)
    if device == "cuda":
        try:
            pipe.unet.to(device)
            pipe.vae.to(device)
            if hasattr(pipe, "text_encoder"):
                pipe.text_encoder.to(device)
            if hasattr(pipe, "controlnet"):
                pipe.controlnet.to(device)
            print("[SD15 Pipeline] UNet/VAE/TextEncoder/ControlNet 모두 CUDA로 정렬 완료.")
        except Exception as e:
            print(f"[WARNING] 서브모델 device 정렬 중 경고: {e}")

    _pipeline = pipe
    return _pipeline


# -----------------------------------------------------------------------------#
# 메인 합성 함수                                                                #
# -----------------------------------------------------------------------------#

def synthesize_image(
    prompt: str,
    product_image: Image.Image,
    mask_image: Image.Image,
    full_image: Image.Image,
    control_weight: float = 1.0,
    ip_adapter_scale: float = 0.7,
) -> Image.Image:
    """
    SD1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)를 사용해서
    '원본 상품 + 새 배경'이 합성된 이미지를 생성하는 함수

    - prompt           : 배경/장면에 대한 텍스트 프롬프트
    - product_image    : 누끼된 제품 RGB
    - mask_image       : 제품 영역 마스크 (흰색=상품, 검정=배경)
    - full_image       : 배경 포함 원본 이미지
    - control_weight   : Depth ControlNet 강도 (0이면 depth 비활성화)
    - ip_adapter_scale : 레퍼런스 이미지 스타일 반영 강도 (0~1 권장)
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded

    if _pipeline is None:
        _load_pipeline()

    pipe = _pipeline
    # diffusers 0.30 이후에는 pipe.device가 없을 수 있어서 방어
    device = getattr(pipe, "device", "cuda" if torch.cuda.is_available() else "cpu")

    print(
        f"[SD15 Synthesis] Running pipeline. Depth Weight: {control_weight}, IP Scale: {ip_adapter_scale}, device={device}"
    )

    # 광고용 네거티브 프롬프트
    negative_prompt = (
        "monochrome, lowres, bad anatomy, worst quality, low quality, blurry, "
        "text, logo, watermark, signature, handwriting, caption, blob, melted, "
        "distorted, deformed, out of frame"
    )

    try:
        # --------------------------------------------------------------
        # 1. 입력 이미지 모드 정리
        # --------------------------------------------------------------
        if product_image.mode not in ("RGB", "RGBA"):
            product_image = product_image.convert("RGB")
        if full_image.mode not in ("RGB", "RGBA"):
            full_image = full_image.convert("RGB")
        if mask_image.mode not in ("L", "RGB", "RGBA"):
            mask_image = mask_image.convert("L")

        # --------------------------------------------------------------
        # 2. Depth 맵은 "배경 포함 원본(full_image)"에서만 추출
        # --------------------------------------------------------------
        depth_map = None
        if control_weight > 0:
            depth_raw = _midas_detector(
                full_image,              # 누끼가 아닌 원본 사용
                detect_resolution=512,
                image_resolution=768,
            )

            depth_np = np.array(depth_raw)
            depth_np = depth_np - depth_np.min()
            if depth_np.max() > 0:
                depth_np = depth_np / depth_np.max()
            depth_np = (depth_np * 255).astype("uint8")
            depth_map = Image.fromarray(depth_np)

        # --------------------------------------------------------------
        # 3. IP-Adapter는 "누끼된 product_image"에서 스타일/색감 가져오기
        # --------------------------------------------------------------
        ip_kwargs = {}
        if _ip_adapter_loaded and ip_adapter_scale > 0:
            pipe.set_ip_adapter_scale(ip_adapter_scale)
            ip_kwargs["ip_adapter_image"] = product_image
            print("[IP-Adapter] ip_adapter_image 및 scale 설정 완료.")
        else:
            pipe.set_ip_adapter_scale(0.0)
            print("[IP-Adapter] 비활성화 (로드 실패 또는 scale <= 0).")

        # --------------------------------------------------------------
        # 4. 난수 시드 (재현성 확보용)
        # --------------------------------------------------------------
        generator = torch.Generator(device=device).manual_seed(0)

        # --------------------------------------------------------------
        # 5. 파이프라인 호출 (Depth on/off 분기)
        # --------------------------------------------------------------
        if depth_map is not None:
            print("[Pipeline] Using ControlNet Depth (from full_image)")
        else:
            print("[Pipeline] Depth disabled → txt2img + (optional) IP-Adapter")

        # fp16 on cuda / fp32 on cpu 자동 처리
        if device == "cuda":
            autocast_ctx = torch.cuda.amp.autocast(dtype=torch.float16)
        else:
            # CPU에서는 autocast 필요 없음
            from contextlib import nullcontext
            autocast_ctx = nullcontext()

        with torch.inference_mode(), autocast_ctx:
            if depth_map is not None:
                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=depth_map,  # depth 맵을 ControlNet 입력으로 사용
                    controlnet_conditioning_scale=control_weight,
                    guidance_scale=8.0,
                    num_inference_steps=20,
                    generator=generator,
                    **ip_kwargs,
                )
            else:
                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=None,
                    controlnet_conditioning_scale=0.0,
                    guidance_scale=9.0,
                    num_inference_steps=40,
                    generator=generator,
                    **ip_kwargs,
                )

        generated_bg = result.images[0]
        del result

        # --------------------------------------------------------------
        # 6. 최종 합성: product_image + 생성 배경
        # --------------------------------------------------------------
        bg_w, bg_h = generated_bg.size
        fg = product_image.resize((bg_w, bg_h), Image.LANCZOS)
        m = mask_image.resize((bg_w, bg_h), Image.LANCZOS).convert("L")

        final_image = Image.composite(fg, generated_bg, m)
        del generated_bg, fg, m

        return final_image

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        raise Exception(f"Image generation failed: {e}")
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            print("[GPU Memory] VRAM cleanup executed.")
            
            
# 입력받은 프롬프트를 바탕으로 홍보용 이미지 출력 (GPU 미사용 - 플레이스홀더 이미지 반환)

def generate_poster_image(prompt: str, product_image_bytes: Optional[bytes] = None) -> bytes:
    """
    GPU를 사용하지 않고 임의의 플레이스홀더 이미지를 생성합니다.
    팀원들과 GPU 공유 시 충돌을 피하기 위한 임시 구현입니다.
    
    Args:
        prompt: 이미지 생성용 프롬프트
        product_image_bytes: 제품 이미지 바이트 (선택사항)
    """
    try:
        prompt = str(prompt).encode("utf-8", errors="ignore").decode("utf-8")
        print(f"[PLACEHOLDER] generating placeholder image for prompt: {prompt}")
        
        if product_image_bytes:
            print(f"[PLACEHOLDER] product image received: {len(product_image_bytes)} bytes")

        # 512x512 크기의 이미지 생성 (랜덤 배경색)
        colors = [
            (255, 182, 193),  # 연한 핑크
            (173, 216, 230),  # 연한 파랑
            (144, 238, 144),  # 연한 초록
            (255, 218, 185),  # 복숭아색
            (221, 160, 221),  # 연한 보라
            (255, 250, 205),  # 레몬색
        ]
        bg_color = random.choice(colors)
        
        # 이미지 생성
        image = Image.new('RGB', (512, 512), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        # product_image가 있으면 합성 (간단한 예시)
        if product_image_bytes:
            try:
                product_img = Image.open(BytesIO(product_image_bytes))
                # 제품 이미지를 작게 리사이즈
                product_img.thumbnail((200, 200))
                # 중앙 하단에 붙이기
                x = (512 - product_img.width) // 2
                y = 512 - product_img.height - 50
                image.paste(product_img, (x, y))
            except Exception as e:
                print(f"[WARNING] Failed to process product image: {e}")
        
        # 테두리 추가
        border_color = tuple(max(0, c - 50) for c in bg_color)
        draw.rectangle([10, 10, 502, 502], outline=border_color, width=5)
        
        # 텍스트 추가 (중앙에 "Generated Image" 표시)
        try:
            # 시스템 기본 폰트 사용
            font = ImageFont.load_default()
        except:
            font = None
        
        text = "Generated Image"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (512 - text_width) // 2
        text_y = (512 - text_height) // 2 - 50
        
        draw.text((text_x, text_y), text, fill=(60, 60, 60), font=font)
        
        # 프롬프트 일부 표시 (짧게)
        prompt_display = prompt[:40] + "..." if len(prompt) > 40 else prompt
        prompt_bbox = draw.textbbox((0, 0), prompt_display, font=font)
        prompt_width = prompt_bbox[2] - prompt_bbox[0]
        prompt_x = (512 - prompt_width) // 2
        prompt_y = text_y + 30
        
        draw.text((prompt_x, prompt_y), prompt_display, fill=(80, 80, 80), font=font)

        # PNG로 변환
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        raise RuntimeError(f"Placeholder image generation error: {e}")
