import base64
from io import BytesIO
from fastapi import APIRouter, HTTPException, Body
from PIL import Image

from backend.app.services.diffusion_service import synthesize_image
# 스키마 Import 경로와 이름을 사용자가 제공한 내용에 맞춰 수정
# 경로는 'backend.app.core.schemas'에 있다고 가정하고, 스키마 이름은 'DiffusionControlRequest/Response' 사용
from backend.app.core.schemas import DiffusionControlRequest, DiffusionControlResponse 

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

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

# ==============================================================================
# API 라우트
# ==============================================================================

@router.post("/synthesize", response_model=DiffusionControlResponse)
async def diffusion_synthesize(request_body: DiffusionControlRequest = Body(...)):
    """
    ControlNet Depth와 IP-Adapter를 활용하여 이미지를 합성
    """
    print("[API] Received synthesis request.")
    
    try:
        # 1. Base64 입력 디코딩 (클라이언트 데이터 -> PIL Image 객체)
        original_image = _base64_to_image(request_body.original_image_b64)
        mask_image = _base64_to_image(request_body.mask_b64)
        
        if original_image is None or mask_image is None:
            raise ValueError("Original image or mask image is missing or invalid.")

        # 2. 서비스 로직 호출
        final_image_pil = synthesize_image(
            prompt=request_body.prompt,
            original_image=original_image,
            mask_image=mask_image,
            control_weight=request_body.control_weight,
            ip_adapter_scale=request_body.ip_adapter_scale
        )

        # 3. PIL Image 객체 인코딩 (PIL Image 객체 -> Base64 문자열)
        final_image_b64 = _image_to_base64(final_image_pil)
        
        print("[API] Synthesis successful. Returning Base64 image.")

        # DiffusionControlResponse 스키마에 맞춰 'image_b64' 인자 사용
        return DiffusionControlResponse(
            image_b64=final_image_b64,
            status="success",
            message="Image synthesis successful."
        )

    except Exception as e:
        print(f"[FATAL] An unexpected error occurred: {e}")
        # 오류가 발생해도 응답 스키마의 기본 필드를 채워서 반환
        raise HTTPException(status_code=500, detail=str(e))