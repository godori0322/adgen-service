# diffusion.py
import asyncio
import base64
from io import BytesIO
import io
import os
from typing import Optional
import numpy as np
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from PIL import Image

from backend.app.services.diffusion_service import synthesize_image
from backend.app.services.segmentation import ProductSegmentation
# 스키마 Import 경로와 이름을 사용자가 제공한 내용에 맞춰 수정
# 경로는 'backend.app.core.schemas'에 있다고 가정하고, 스키마 이름은 'DiffusionControlRequest/Response' 사용
from backend.app.core.schemas import DiffusionControlRequest, DiffusionControlResponse, DiffusionAutoRequest 

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

# ----------------------------------------------------------------------------
# 요청 큐/세마포어 (동시 생성 억제)
# ----------------------------------------------------------------------------
_max_concurrency = int(os.getenv("DIFFUSION_MAX_CONCURRENCY", "1"))
_request_semaphore = asyncio.Semaphore(max(1, _max_concurrency))

# ------------------------------------------------------------------------------
# 전역 세그멘테이션 모델 (lazy load)
# ------------------------------------------------------------------------------
_segmentation_model: Optional[ProductSegmentation] = None

def _get_segmentation_model() -> ProductSegmentation:
    global _segmentation_model
    if _segmentation_model is None:
        try:
            _segmentation_model = ProductSegmentation()
            print("[Segmentation] MobileSAM 로드 완료.")
        except Exception as exc:
            print(f"[Segmentation][ERROR] 모델 로드 실패: {exc}")
            raise HTTPException(status_code=500, detail="Segmentation model load failed.")
    return _segmentation_model

# ==============================================================================
# 유틸리티 함수 (Base64 변환은 API 경계에서 처리)
# ==============================================================================

def _base64_to_image(base64_string: str) -> Image.Image:
    """Base64 문자열을 PIL Image 객체로 변환합니다."""
    try:
        if not base64_string:
            return None
        # Base64 문자열이 'data:image/png;base64,'와 같은 프리픽스를 포함할 경우 제거
        if "," in base64_string:
            base64_string = base64_string.split(",", 1)[1]
        
        image_bytes = base64.b64decode(base64_string)
        return Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        print(f"[ERROR] Base64 to image conversion failed: {e}")
        raise ValueError(f"Invalid Base64 image data provided: {e}")

def _image_to_base64(image: Image.Image) -> str:
    """PIL Image 객체를 Base64 문자열로 변환합니다."""
    buffered = BytesIO()
    # JPEG보다 PNG가 손실이 적고, 투명도 지원이 용이합니다.
    image.save(buffered, format="PNG") 
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def _mask_array_to_pil(mask_array: np.ndarray) -> Image.Image:
    """SAM이 반환한 마스크(ndarray)를 '흑백 L' 모드 PIL 이미지로 변환."""
    scaled = np.clip(mask_array * 255.0, 0, 255).astype("uint8")
    return Image.fromarray(scaled, mode="L")


def _run_auto_synthesis(
    original_image: Image.Image,    # 업로된 전체 이미지
    prompt: str,
    control_weight: float,
    ip_adapter_scale: float,
) -> Image.Image:
    """세그멘테이션 → 합성까지 실행하고 최종 이미지를 PIL로 반환."""
    model = _get_segmentation_model()
    # 1) segmentation 전체 이미지 기준으로 누끼따기
    mask_array, cutout_image = model.remove_background(original_image)  # sam으로 마스크 + 컷아웃 get

    # 2) 마스크/제품 RGB 준비
    mask_image = _mask_array_to_pil(mask_array)     # 마스크(nparray 0~1) -> l 모드로 pil 이미지
    # 컷아웃 RGBA -> IP-Adapter/ControlNet용 RGB 이미지로 변경(추가)
    product_rgb = cutout_image.convert("RGB")

    # 3) diffusion_service.synthesize_image 호출
    return synthesize_image(
        prompt=prompt,
        product_image=product_rgb,     # 누끼된 상품
        mask_image=mask_image,         # 상품 마스크
        full_image=original_image,     # 배경 포함 원본 (Depth 용)
        control_weight=control_weight,
        ip_adapter_scale=ip_adapter_scale,
    )

# ==============================================================================
# API 라우트
# ==============================================================================

@router.post("/synthesize/auto", response_model=DiffusionControlResponse)
async def diffusion_synthesize_auto(request_body: DiffusionAutoRequest = Body(...)):
    """
    제품 이미지만 받아서
    1) SAM으로 누끼/마스크 추출
    2) 추출된 마스크와 컷아웃을 이용해 배경 합성까지 한 번에 처리
    """
    print("[API] Received auto synthesis request.")

    try:
        original_image = _base64_to_image(request_body.product_image_b64)
        if original_image is None:
            raise ValueError("Product image is missing or invalid.")

        async with _request_semaphore:
            final_image_pil = await asyncio.to_thread(
                _run_auto_synthesis,
                original_image=original_image,
                prompt=request_body.prompt or "",
                control_weight=request_body.control_weight,
                ip_adapter_scale=request_body.ip_adapter_scale,
            )
        final_image_b64 = _image_to_base64(final_image_pil)
        print("[API] Auto synthesis successful. Returning Base64 image.")

        return DiffusionControlResponse(
            image_b64=final_image_b64,
            status="success",  # type: ignore[arg-type]
            message="Image synthesis successful.",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL][AUTO] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/synthesize/auto/upload",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "누끼+배경 합성된 최종 PNG 이미지",
        }
    },
)
async def diffusion_synthesize_auto_upload(
    file: UploadFile = File(...),
    prompt: str = Form(
        "A cinematic, studio-lit product hero shot on a clean background"
    ),
    control_weight: float = Form(1.0),
    ip_adapter_scale: float = Form(0.7),
):
    """
    segmentation_test.py와 동일하게 파일 업로드를 받아
    누끼+배경 합성을 한 번에 처리하는 엔드포인트.
    """
    print("[API] Received auto synthesis upload request.")
    try:
        original_image = Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image upload.")

    try:
        async with _request_semaphore:
            final_image_pil = await asyncio.to_thread(
                _run_auto_synthesis,
                original_image=original_image,
                prompt=prompt or "",
                control_weight=control_weight,
                ip_adapter_scale=ip_adapter_scale,
            )
        print("[API] Auto synthesis (upload) successful. Returning PNG image.")

        buf = io.BytesIO()
        final_image_pil.save(buf, format="PNG")
        buf.seek(0)

        # Swagger에서 이미지로 바로 미리보기 하도록 StreamingResponse 사용
        return StreamingResponse(
            buf,
            media_type="image/png",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL][AUTO][UPLOAD] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
