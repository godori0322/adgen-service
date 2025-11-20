import torch
from io import BytesIO
from PIL import Image
from diffusers import (
    StableDiffusionXLControlNetPipeline, 
    ControlNetModel,
    AutoencoderKL,
    EulerAncestralDiscreteScheduler
)
from controlnet_aux import MidasDetector
import base64
import os

# IP-Adapter 모델 ID 및 경로 설정
IP_ADAPTER_MODEL_ID = "h94/IP-Adapter"
IP_ADAPTER_WEIGHT_NAME = "ip-adapter-plus_sdxl_vit-h.safetensors"
IP_ADAPTER_SUBFOLDER = "sdxl_models" 

# 전역 변수 설정 (모델 캐싱)
_pipeline = None
_midas_detector = None
_ip_adapter_loaded = False 

# ======================================================================
# 모델 로딩 & 캐싱 
# ======================================================================

def _load_pipeline():
    """
    ControlNet Depth와 IP-Adapter를 통합한 SDXL 파이프라인 로드 및 캐싱을 담당합니다.
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded
    print("[SDXL Pipeline] Loading base models...")
    
    # GPU 사용 가능 여부 확인 및 Device 설정
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # GPU 사용 시 메모리 효율적인 데이터 타입 (float16) 사용
    MODEL_DTYPE = torch.float16 if device == "cuda" else torch.float32 
    
    # SDXL 기본 모델 & VAE 로드
    base_model = "stabilityai/stable-diffusion-xl-base-1.0"
    vae = AutoencoderKL.from_pretrained(
        "madebyollin/sdxl-vae-fp16-fix",
        torch_dtype=MODEL_DTYPE
    ).to(device)
    
    # ControlNet (Depth) 모델 로드
    controlnet_depth = ControlNetModel.from_pretrained(
        "diffusers/controlnet-depth-sdxl-1.0",
        torch_dtype=MODEL_DTYPE
    ).to(device)
    
    # StableDiffusionXLControlNetPipeline (ControlNet 통합 파이프라인) 사용
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        base_model,
        vae=vae,
        controlnet=controlnet_depth,
        torch_dtype=MODEL_DTYPE,
    ).to(device)
    
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

    # 메모리 최적화 설정 (GPU일 때만 xformers)
    if device == "cuda":
        pipe.enable_xformers_memory_efficient_attention()
        print("[SDXL Pipeline] xformers 활성화됨.")

    # 선택: VAE slicing으로 메모리 절약
    pipe.enable_vae_slicing()

    # Midas Detector (Depth 맵 전처리기) 로드
    print("[Midas Detector] Depth 전처리기 로드 중...")
    _midas_detector = MidasDetector.from_pretrained("lllyasviel/ControlNet").to(device)
    print("[Midas Detector] Depth 전처리기 성공적으로 로드됨.")

    # IP-Adapter (이미지 스타일 제어 모델) 로드 
    print("[IP-Adapter] Loading IP-Adapter into the pipeline using pipe.load_ip_adapter...")
    try:
        pipe.load_ip_adapter(
            IP_ADAPTER_MODEL_ID,
            subfolder=IP_ADAPTER_SUBFOLDER, 
            weight_name=IP_ADAPTER_WEIGHT_NAME, 
            torch_dtype=MODEL_DTYPE,
        )
        print(f"[IP-Adapter] {os.path.join(IP_ADAPTER_SUBFOLDER, IP_ADAPTER_WEIGHT_NAME)} 로드 성공.")
        _ip_adapter_loaded = True 
    except Exception as e:
        print(f"[WARNING] IP-Adapter 로드 실패: {e}. 스타일 제어 기능이 비활성화됩니다.")
        _ip_adapter_loaded = False
        
    _pipeline = pipe
    return _pipeline

# ======================================================================
# 이미지 합성 메인 서비스
# ======================================================================

def synthesize_image(
    prompt: str,
    original_image: Image.Image,
    mask_image: Image.Image,
    control_weight: float = 1.0,
    ip_adapter_scale: float = 0.7,
) -> Image.Image:
    """
    ControlNet Depth와 IP-Adapter를 활용하여 이미지를 합성하고 PIL Image 객체로 반환합니다.
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded
    
    if _pipeline is None:
        _load_pipeline()

    print(f"[SDXL Synthesis] Running pipeline. Depth Weight: {control_weight}, IP Scale: {ip_adapter_scale}")
    
    try:
        negative_prompt = (
            "blurry, low quality, distortion, noise, artifacts, ugly, deformed, text, signature"
        )

        # --------------------------------------------------
        # 1. Depth 맵 생성 (ControlNet용 conditioning 이미지)
        # --------------------------------------------------
        depth_map = _midas_detector(
            original_image,
            detect_resolution=512,
            image_resolution=1024,
        )

        # --------------------------------------------------
        # 2. IP-Adapter 설정 (임베딩 직접 건드리지 않음)
        # --------------------------------------------------
        ip_kwargs = {}
        if _ip_adapter_loaded and ip_adapter_scale > 0:
            # scale 설정 (하나만 쓴다고 가정)
            _pipeline.set_ip_adapter_scale(ip_adapter_scale)
            # 원본 이미지를 스타일 레퍼런스로 사용
            ip_kwargs["ip_adapter_image"] = original_image
            print("[IP-Adapter] ip_adapter_image 및 scale 설정 완료.")
        else:
            print("[IP-Adapter] 비활성화 상태이거나 scale <= 0. IP-Adapter 없이 진행합니다.")

        # --------------------------------------------------
        # 3. 난수 시드 (재현성)
        # --------------------------------------------------
        generator = torch.Generator(device=_pipeline.device).manual_seed(0)

        # --------------------------------------------------
        # 4. 파이프라인 호출
        #    ★ 여기서 더 이상 encode_prompt / prepare_ip_adapter_image_embeds 안 씀
        #    ★ prompt_embeds, ip_adapter_image_embeds도 직접 전달 안 함
        # --------------------------------------------------
        result = _pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=depth_map,                          # ControlNet depth 입력
            controlnet_conditioning_scale=control_weight,
            guidance_scale=7.5,
            num_inference_steps=29,
            generator=generator,
            **ip_kwargs,                              # ip_adapter_image=original_image (옵션)
        )

        images = result.images

        # --------------------------------------------------
        # 5. 후처리: 제품 + 배경 합성
        # --------------------------------------------------
        generated_image = images[0]
        
        # 크기 일치
        target_size = generated_image.size 
        resized_original_image = original_image.resize(target_size)
        resized_mask_image = mask_image.resize(target_size)
        
        # 마스크 포맷 변환 (L 모드 - Grayscale)
        final_mask_for_composite = resized_mask_image.convert("L")
        
        # Image.composite을 사용하여 원본 제품을 AI 생성 배경 위에 최종적으로 합성
        final_image = Image.composite(resized_original_image, generated_image, final_mask_for_composite)

        # PIL Image 객체로 반환
        return final_image

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        raise Exception(f"Image generation failed: {e}")
    finally:
        # VRAM 정리 (메모리 누수 해결)
        if torch.cuda.is_available():
            torch.cuda.empty_cache() 
            print("[GPU Memory] VRAM cleanup executed.")
