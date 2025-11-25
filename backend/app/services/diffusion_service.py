#diffusion_service 원본

# diffusion_service.py

import os

# main.py에서 이미 설정했지만, 단독 실행/테스트를 대비해 한 번 더 명시
os.environ.setdefault("HF_HOME", "/home/shared/models")
os.environ.setdefault("DIFFUSERS_CACHE", "/home/shared/models")
os.environ.setdefault("TRANSFORMERS_CACHE", "/home/shared/models")
os.environ.setdefault("TORCH_HOME", "/home/shared/models")

import torch
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
)
from controlnet_aux import MidasDetector
import numpy as np

# -----------------------------------------------------------------------------#
# 설정: SD 1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)                          #
# -----------------------------------------------------------------------------#

HF_CACHE_DIR = "/home/shared/models"  # 공용 캐시/모델 디렉터리 경로 상수

SD15_MODEL_ID = "runwayml/stable-diffusion-v1-5"
# 여기를 로컬 경로가 아니라 허깅페이스 모델 ID로 둬야 config.json을 찾을 수 있음
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
    model_dtype = torch.float16 if device == "cuda" else torch.float32

    # 1) ControlNet(Depth) 로드
    controlnet_depth = ControlNetModel.from_pretrained(
        CONTROLNET_DEPTH_ID,
        cache_dir=HF_CACHE_DIR,      # 반드시 /home/shared/models 아래에 캐시/모델 생성
        torch_dtype=model_dtype,
    ).to(device)

    # 2) StableDiffusionControlNetPipeline 로드 (Base: SD 1.5)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        SD15_MODEL_ID,
        controlnet=controlnet_depth,
        cache_dir=HF_CACHE_DIR,      # 동일하게 shared 캐시 사용
        torch_dtype=model_dtype,
        safety_checker=None,         # 광고용이라면 별도 필터링에서 처리
    ).to(device)

    # 3) 스케줄러/메모리 최적화
    try:
        if device == "cuda":
            pipe.enable_xformers_memory_efficient_attention()
            print("[SD15 Pipeline] xformers 활성화됨.")
    except Exception as e:
        print(f"[WARNING] xformers 활성화 실패: {e}")

    pipe.enable_vae_slicing()

    # 4) Depth 전처리기(Midas) 로드
    print("[Midas Detector] Depth 전처리기 로드 중...")
    _midas_detector = MidasDetector.from_pretrained(
        "lllyasviel/ControlNet",
        cache_dir=HF_CACHE_DIR,      # 이쪽도 shared/models에 캐시
    ).to(device)
    print("[Midas Detector] Depth 전처리기 성공적으로 로드됨.")

    # 5) IP-Adapter(SD1.5) 로드
    global _ip_adapter_loaded
    print("[IP-Adapter] SD1.5용 IP-Adapter 로드 중...")
    try:
        # load_ip_adapter 내부도 HF_HOME / HF_CACHE_DIR를 사용함
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

    _pipeline = pipe
    return _pipeline


# -----------------------------------------------------------------------------#
# 메인 합성 함수                                                                #
# -----------------------------------------------------------------------------#

def synthesize_image(
    prompt: str,
    original_image: Image.Image,
    mask_image: Image.Image,
    control_weight: float = 1.0,
    ip_adapter_scale: float = 0.7,
) -> Image.Image:
    """
    SD1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)를 사용해서
    '원본 상품 + 새 배경'이 합성된 이미지를 생성하는 함수

    - prompt           : 배경/장면에 대한 텍스트 프롬프트
    - original_image   : 상품이 포함된 원본/누끼 이미지 (PIL)
    - mask_image       : 상품 영역 마스크 (흰색=상품, 검정=배경)
    - control_weight   : Depth ControlNet 강도 (0이면 depth 비활성화)
    - ip_adapter_scale : 레퍼런스 이미지 스타일 반영 강도 (0.1까지 반영가능)
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded

    if _pipeline is None:
        _load_pipeline()

    pipe = _pipeline
    device = pipe.device

    print(
        f"[SD15 Synthesis] Running pipeline. Depth Weight: {control_weight}, IP Scale: {ip_adapter_scale}"
    )

    # 광고용 네거티브 프롬프트
    negative_prompt = (
        "monochrome, lowres, bad anatomy, worst quality, low quality, blurry, text, logo, watermark, signature, handwriting, caption, blob, melted, distorted, deformed, out of frame"
    )

    try:
        # --------------------------------------------------------------
        # 1. 입력 이미지 전처리 (모드 통일)
        # --------------------------------------------------------------
        if original_image.mode not in ("RGB", "RGBA"):
            original_image = original_image.convert("RGB")
        if mask_image.mode not in ("L", "RGB", "RGBA"):
            mask_image = mask_image.convert("L")

        # --------------------------------------------------------------
        # 2. Depth 맵 생성 (control_weight == 0이면 비활성화)
        # --------------------------------------------------------------
        depth_map = None

        if control_weight > 0:
            depth_raw = _midas_detector(
                original_image,
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
        # 3. IP-Adapter 스케일 설정
        # --------------------------------------------------------------
        ip_kwargs = {}
        if _ip_adapter_loaded and ip_adapter_scale > 0:
            pipe.set_ip_adapter_scale(ip_adapter_scale)
            # 여기서 original_image는 diffusion.py에서 전달한 product_rgb (누끼 컷아웃)임
            ip_kwargs["ip_adapter_image"] = original_image
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
            print("[Pipeline] Using ControlNet Depth")
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=depth_map,  # ControlNet depth conditioning
                controlnet_conditioning_scale=control_weight,
                guidance_scale=8.0,
                num_inference_steps=40,
                generator=generator,
                **ip_kwargs,
            )
        else:
            print("[Pipeline] Depth disabled → txt2img + (optional) IP-Adapter")
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

        # --------------------------------------------------------------
        # 6. 최종 합성: 원본 상품 + 생성 배경
        # --------------------------------------------------------------
        bg_w, bg_h = generated_bg.size
        fg = original_image.resize((bg_w, bg_h), Image.LANCZOS)
        m = mask_image.resize((bg_w, bg_h), Image.LANCZOS).convert("L")

        final_image = Image.composite(fg, generated_bg, m)

        return final_image

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        raise Exception(f"Image generation failed: {e}")
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("[GPU Memory] VRAM cleanup executed.")
