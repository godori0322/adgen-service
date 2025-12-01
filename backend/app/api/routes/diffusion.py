# diffusion.py
import asyncio
import base64
import io
import os
from io import BytesIO
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from PIL import Image

from backend.app.services.diffusion_service import (
    synthesize_image,
    generate_poster_image,
    run_auto_synthesis,
    generate_poster_with_product_b64
)
from backend.app.services.segmentation import ProductSegmentation
from backend.app.core.diffusion_presets import resolve_preset
from backend.app.core.schemas import (
    DiffusionControlRequest,
    DiffusionControlResponse,
    DiffusionAutoRequest,
    CompositionMode,
)

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

# ----------------------------------------------------------------------------
# 요청 동시성 제한 (GPU/CPU 보호용)
# ----------------------------------------------------------------------------
_max_concurrency = int(os.getenv("DIFFUSION_MAX_CONCURRENCY", "1"))
_request_semaphore = asyncio.Semaphore(max(1, _max_concurrency))

# ----------------------------------------------------------------------
# 전역 세그멘테이션 모델 (lazy load)
# ----------------------------------------------------------------------
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


# ======================================================================
# 유틸리티 함수 (Base64 변환은 API 경계에서 처리)
# ======================================================================

# def _base64_to_image(base64_string: str) -> Optional[Image.Image]:
#     """Base64 문자열을 PIL Image 객체로 변환."""
#     try:
#         if not base64_string:
#             return None
#         # "data:image/png;base64,..." 같은 prefix 제거
#         if "," in base64_string:
#             base64_string = base64_string.split(",", 1)[1]

#         image_bytes = base64.b64decode(base64_string)
#         return Image.open(BytesIO(image_bytes)).convert("RGB")
#     except Exception as e:
#         print(f"[ERROR] Base64 to image conversion failed: {e}")
#         raise ValueError(f"Invalid Base64 image data provided: {e}")


def _image_to_base64(image: Image.Image) -> str:
    """PIL Image 객체를 Base64 문자열로 변환."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


# def _mask_array_to_pil(mask_array: np.ndarray) -> Image.Image:
#     """SAM 마스크(ndarray)를 흑백(L) 모드 PIL 이미지로 변환."""
#     scaled = np.clip(mask_array * 255.0, 0, 255).astype("uint8")
#     return Image.fromarray(scaled, mode="L")


def _parse_optional_float(value: str | None) -> float | None:
    """
    Swagger Form에서 넘어오는 값은 빈 문자열("")일 수 있으므로:
    - None 또는 ""  → None (override 안함)
    - 나머지        → float(value)
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid float value: {value}",
        )


# ======================================================================
# 세그멘테이션 + 프리셋 해석 + 합성 실행
# ======================================================================

def _run_auto_synthesis(
    original_image: Image.Image,   # 업로드 된 전체 이미지
    prompt: str,
    mode: CompositionMode = CompositionMode.balanced,  # 의도 모드
    control_weight: float | None = None,
    ip_adapter_scale: float | None = None,
) -> Image.Image:
    """
    1) 세그멘테이션 (MobileSAM + SAM)
    2) CompositionMode 프리셋 + (옵션) override 해석
    3) diffusion_service.synthesize_image 호출
    """
    model = _get_segmentation_model()

    # 1) segmentation: 전체 이미지 기준으로 누끼 따기
    mask_array, cutout_image = model.remove_background(original_image)

    # 2) 마스크/제품 RGB 준비
    mask_image = _mask_array_to_pil(mask_array)
    product_rgb = cutout_image.convert("RGB")

    # 3) CompositionMode + override -> 최종 수치
    cw, ip = resolve_preset(
        mode=mode,
        override_control=control_weight,
        override_ip=ip_adapter_scale,
    )
    print(f"[Preset] mode={mode}, control={cw}, ip={ip}")

    # 4) diffusion_service.synthesize_image 호출
    return synthesize_image(
        prompt=prompt,
        product_image=product_rgb,   # 누끼된 상품
        mask_image=mask_image,       # 상품 마스크
        full_image=original_image,   # 배경 포함 원본 (Depth 용)
        control_weight=cw,
        ip_adapter_scale=ip,
    )


# ======================================================================
# API 라우트
# ======================================================================

# @router.post("/synthesize/auto", response_model=DiffusionControlResponse)
# async def diffusion_synthesize_auto(request_body: DiffusionAutoRequest = Body(...)):
#     """
#     JSON Base64 버전:
#     - product_image_b64만 받아서
#       1) SAM으로 누끼/마스크 추출
#       2) CompositionMode 프리셋 + (옵션) override 적용
#       3) 최종 합성 이미지 Base64로 반환
#     """
#     print("[API] Received auto synthesis request.")

#     try:
#         original_image = _base64_to_image(request_body.product_image_b64)
#         if original_image is None:
#             raise ValueError("Product image is missing or invalid.")

#         # CPU/GPU 작업을 백그라운드 스레드에서 실행 + 동시성 제한
#         async with _request_semaphore:
#             final_image_pil = await asyncio.to_thread(
#                 _run_auto_synthesis,
#                 original_image=original_image,
#                 prompt=request_body.prompt or "",
#                 mode=request_body.composition_mode,
#                 control_weight=request_body.control_weight,
#                 ip_adapter_scale=request_body.ip_adapter_scale,
#             )
#         final_image_b64 = _image_to_base64(final_image_pil)
#         print("[API] Auto synthesis successful. Returning Base64 image.")

#         return DiffusionControlResponse(
#             image_b64=final_image_b64,
#             status="success",   # BaseResponse 상속 구조 맞춤
#             message="Image synthesis successful.",
#         )

#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[FATAL][AUTO] An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize/auto", response_model=DiffusionControlResponse)
async def diffusion_synthesize_auto(request_body: DiffusionAutoRequest = Body(...)):
    """
    JSON Base64 버전:
    - product_image_b64만 받아서
      1) 세그멘테이션 + 프리셋 + 합성 (서비스 레이어)
      2) 최종 이미지를 Base64로 반환
    """
    print("[API] Received auto synthesis request.")

    try:
        async with _request_semaphore:
            image_bytes = await asyncio.to_thread(
                generate_poster_with_product_b64,
                request_body.prompt or "",
                request_body.product_image_b64,
                request_body.composition_mode,
                request_body.control_weight,
                request_body.ip_adapter_scale,
            )

        final_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        print("[API] Auto synthesis successful. Returning Base64 image.")

        return DiffusionControlResponse(
            image_b64=final_image_b64,
            status="success",
            message="Image synthesis successful.",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL][AUTO] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))




# @router.post(
#     "/synthesize/auto/upload",
#     response_class=StreamingResponse,
#     responses={
#         200: {
#             "content": {"image/png": {}},
#             "description": "누끼+배경 합성된 최종 PNG 이미지",
#         }
#     },
# )
# async def diffusion_synthesize_auto_upload(
#     file: UploadFile = File(...),
#     prompt: str = Form(
#         "A cinematic, studio-lit product hero shot on a clean background"
#     ),
#     composition_mode: CompositionMode = Form(
#         CompositionMode.balanced,
#         description="합성 모드 (rigid/balanced/creative)",
#     ),
#     # Swagger Form에서는 빈 문자열("")이 들어올 수 있으므로 raw 문자열로 받음
#     control_weight_raw: str | None = Form(
#         None,
#         description="프리셋 ControlNet 값을 덮어쓰고 싶을 때만 지정 (비우면 프리셋 사용)",
#     ),
#     ip_adapter_scale_raw: str | None = Form(
#         None,
#         description="프리셋 IP_Adapter 값을 덮어쓰고 싶을 때만 지정 (비우면 프리셋 사용)",
#     ),
# ):
#     """
#     파일 업로드 버전:
#     1) 파일로 이미지 업로드
#     2) MobileSAM + SAM으로 누끼/마스크 추출
#     3) CompositionMode 프리셋 + (옵션) control/ip override 적용
#     4) PNG 이미지로 바로 응답
#     """
#     print("[API] Received auto synthesis upload request.")

#     try:
#         original_image = Image.open(file.file).convert("RGB")
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid image upload.")

#     # 문자열 → float/None 변환 ("" → None)
#     control_weight = _parse_optional_float(control_weight_raw)
#     ip_adapter_scale = _parse_optional_float(ip_adapter_scale_raw)

#     try:
#         async with _request_semaphore:
#             final_image_pil = await asyncio.to_thread(
#                 _run_auto_synthesis,
#                 original_image=original_image,
#                 prompt=prompt or "",
#                 mode=composition_mode,
#                 control_weight=control_weight,
#                 ip_adapter_scale=ip_adapter_scale,
#             )
#         print("[API] Auto synthesis (upload) successful. Returning PNG image.")

#         buf = io.BytesIO()
#         final_image_pil.save(buf, format="PNG")
#         buf.seek(0)

#         return StreamingResponse(
#             buf,
#             media_type="image/png",
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"[FATAL][AUTO][UPLOAD] An unexpected error occurred: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


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
    composition_mode: CompositionMode = Form(
        CompositionMode.balanced,
        description="합성 모드 (rigid/balanced/creative)",
    ),
    control_weight_raw: str | None = Form(
        None,
        description="프리셋 ControlNet 값을 덮어쓰고 싶을 때만 지정 (비우면 프리셋 사용)",
    ),
    ip_adapter_scale_raw: str | None = Form(
        None,
        description="프리셋 IP_Adapter 값을 덮어쓰고 싶을 때만 지정 (비우면 프리셋 사용)",
    ),
):
    print("[API] Received auto synthesis upload request.")

    try:
        original_image = Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image upload.")

    control_weight = _parse_optional_float(control_weight_raw)
    ip_adapter_scale = _parse_optional_float(ip_adapter_scale_raw)

    try:
        async with _request_semaphore:
            final_image_pil = await asyncio.to_thread(
                run_auto_synthesis,
                original_image,
                prompt or "",
                composition_mode,
                control_weight,
                ip_adapter_scale,
            )

        print("[API] Auto synthesis (upload) successful. Returning PNG image.")

        buf = io.BytesIO()
        final_image_pil.save(buf, format="PNG")
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="image/png",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL][AUTO][UPLOAD] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ----------------------------------------------------------------------------
# 기존 포스터 생성 엔드포인트 (prompt + optional product image)
# ----------------------------------------------------------------------------
@router.post("/generate")
async def generate_image(
    prompt: str = Form(..., description="이미지 생성용 프롬프트"),
    product_image: Optional[UploadFile] = File(
        None,
        description="제품 사진, 배경과 합성용(선택)",
    ),
):
    """
    multipart/form-data로 이미지 생성 요청을 받는 엔드포인트.
    - prompt: 텍스트 필드
    - product_image: 파일 (선택사항)
    """
    try:
        product_image_bytes = None
        if product_image:
            product_image_bytes = await product_image.read()

        # 동시성 제한 + 백그라운드 스레드에서 포스터 생성
        async with _request_semaphore:
            image_bytes = await asyncio.to_thread(
                generate_poster_image,
                prompt,
                product_image_bytes,
            )
        image_stream = io.BytesIO(image_bytes)
        return StreamingResponse(image_stream, media_type="image/png")
    except Exception as e:
        print(f"[FATAL][GENERATE] An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
