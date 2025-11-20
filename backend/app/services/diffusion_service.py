# diffusion_service.py

import torch
from io import BytesIO
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
)
from controlnet_aux import MidasDetector
import base64

# -----------------------------------------------------------------------------
# 설정: SD 1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)
# -----------------------------------------------------------------------------
SD15_MODEL_ID = "runwayml/stable-diffusion-v1-5"
CONTROLNET_DEPTH_ID = "lllyasviel/control_v11f1p_sd15_depth"
IP_ADAPTER_MODEL_ID = "h94/IP-Adapter"
IP_ADAPTER_SUBFOLDER = "models"
IP_ADAPTER_WEIGHT_NAME = "ip-adapter_sd15.bin"  # SD1.5용 IP-Adapter 가중치

# 전역 캐시
_pipeline = None
_midas_detector = None
_ip_adapter_loaded = False


# -----------------------------------------------------------------------------
# (필요하면 쓰도록 남겨두는) Base64 <-> PIL 유틸
# -----------------------------------------------------------------------------
def pil_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    """PIL 이미지를 base64 문자열로 변환."""
    buf = BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def base64_to_pil(b64: str) -> Image.Image:
    """base64 문자열을 PIL 이미지로 변환."""
    data = base64.b64decode(b64)
    img = Image.open(BytesIO(data))
    return img.convert("RGBA")


# -----------------------------------------------------------------------------
# 파이프라인 로딩
# -----------------------------------------------------------------------------
def _load_pipeline():
    """
    SD 1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)를 모두 로드하고
    전역 변수에 캐싱하는 함수.
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded

    if _pipeline is not None:
        return _pipeline

    print("[SD15 Pipeline] Loading base models...")

    # 디바이스 / dtype
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_dtype = torch.float16 if device == "cuda" else torch.float32

    # 1) ControlNet(Depth) 로드
    controlnet_depth = ControlNetModel.from_pretrained(
        CONTROLNET_DEPTH_ID,
        torch_dtype=model_dtype,
    ).to(device)

    # 2) StableDiffusionControlNetPipeline 로드 (Base: SD 1.5)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        SD15_MODEL_ID,
        controlnet=controlnet_depth,
        torch_dtype=model_dtype,
        safety_checker=None,  # 광고용 콘텐츠라면 안전필터는 필요 시 별도로 처리
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
        "lllyasviel/ControlNet"
    ).to(device)
    print("[Midas Detector] Depth 전처리기 성공적으로 로드됨.")

    # 5) IP-Adapter(SD1.5) 로드
    global _ip_adapter_loaded
    print("[IP-Adapter] SD1.5용 IP-Adapter 로드 중...")
    try:
        pipe.load_ip_adapter(
            IP_ADAPTER_MODEL_ID,
            subfolder=IP_ADAPTER_SUBFOLDER,
            weight_name=IP_ADAPTER_WEIGHT_NAME,
        )
        # 기본 스케일은 0으로 두고, 합성 함수에서 켜기
        pipe.set_ip_adapter_scale(0.0)
        _ip_adapter_loaded = True
        print(
            f"[IP-Adapter] {IP_ADAPTER_SUBFOLDER}/{IP_ADAPTER_WEIGHT_NAME} 로드 성공."
        )
    except Exception as e:
        print(f"[WARNING] IP-Adapter 로드 실패: {e}. 우선 ControlNet만 사용합니다.")
        _ip_adapter_loaded = False

    _pipeline = pipe
    return _pipeline


# -----------------------------------------------------------------------------
# 메인 합성 함수
# -----------------------------------------------------------------------------
def synthesize_image(
    prompt: str,
    original_image: Image.Image,
    mask_image: Image.Image,
    control_weight: float = 1.0,
    ip_adapter_scale: float = 0.7,
) -> Image.Image:
    """
    SD1.5 + ControlNet(Depth) + IP-Adapter(SD1.5)를 사용해서
    '원본 상품 + 새 배경'이 합성된 이미지를 생성.

    - prompt: 배경/장면에 대한 텍스트 프롬프트
    - original_image: 상품이 포함된 원본 이미지 (PIL)
    - mask_image: 상품 영역 마스크 (흰색=상품, 검정=배경)
    - control_weight: Depth ControlNet 강도
    - ip_adapter_scale: 레퍼런스 이미지(=original_image) 스타일 반영 강도 (0이면 끔)
    """
    global _pipeline, _midas_detector, _ip_adapter_loaded

    if _pipeline is None:
        _load_pipeline()

    pipe = _pipeline
    device = pipe.device

    print(
        f"[SD15 Synthesis] Running pipeline. Depth Weight: {control_weight}, IP Scale: {ip_adapter_scale}"
    )

    # 광고용으로 자주 쓰이는 네거티브 프롬프트(노이즈/깨짐/텍스트 제거)
    negative_prompt = (
        "monochrome, lowres, bad anatomy, worst quality, low quality, blurry, text, logo, watermark, signature"
    )

    try:
        # --------------------------------------------------------------
        # 1. 입력 이미지 전처리 (모드 통일)
        # --------------------------------------------------------------
        if original_image.mode not in ("RGB", "RGBA"):
            original_image = original_image.convert("RGB")
        if mask_image.mode not in ("L", "RGB", "RGBA"):
            mask_image = mask_image.convert("L")

        # ControlNet depth는 해상도 크게 민감하지 않지만,
        # 512~768 정도에서 안정적으로 동작 → 여기서는 image_resolution=768 사용
        depth_input = original_image  # 사이즈는 MidasDetector 안에서 처리

        # --------------------------------------------------------------
        # 2. Depth 맵 생성
        # --------------------------------------------------------------
        depth_map = _midas_detector(
            depth_input,
            detect_resolution=512,
            image_resolution=768,
        )

        # --------------------------------------------------------------
        # 3. IP-Adapter 스케일 설정
        # --------------------------------------------------------------
        ip_kwargs = {}
        if _ip_adapter_loaded and ip_adapter_scale > 0:
            pipe.set_ip_adapter_scale(ip_adapter_scale)
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
        # 5. SD1.5 + ControlNet + (선택적) IP-Adapter 실행
        #    - 텍스트/이미지 임베딩은 모두 파이프라인에 맡김
        # --------------------------------------------------------------
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=depth_map,  # ControlNet depth conditioning
            controlnet_conditioning_scale=control_weight,
            guidance_scale=7.5,
            num_inference_steps=30,
            generator=generator,
            **ip_kwargs,  # ip_adapter_image=original_image (옵션)
        )

        generated_bg = result.images[0]  # 생성된 배경 이미지 (PIL)

        # --------------------------------------------------------------
        # 6. 최종 합성: 원본 상품 + 생성 배경
        # --------------------------------------------------------------
        bg_size = generated_bg.size  # (W, H)
        resized_original = original_image.resize(bg_size, Image.LANCZOS)
        resized_mask = mask_image.resize(bg_size, Image.LANCZOS)

        # 마스크는 흑백(L)로 변환
        final_mask = resized_mask.convert("L")

        # Image.composite:
        #   - 마스크 흰색 → 원본 상품 유지
        #   - 마스크 검정 → 새로 생성된 배경 사용
        final_image = Image.composite(
            resized_original,  # foreground (상품)
            generated_bg,      # background (AI 생성 배경)
            final_mask,
        )

        return final_image

    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")
        raise Exception(f"Image generation failed: {e}")
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("[GPU Memory] VRAM cleanup executed.")
