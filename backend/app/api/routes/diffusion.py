# diffusion.py

from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from backend.app.services.diffusion_service import generate_poster_image
from typing import Optional
import io

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

@router.post("/generate")
async def generate_image(
    prompt: str = Form(..., description="이미지 생성용 프롬프트"),
    product_image: Optional[UploadFile] = File(None, description="제품 사진, 배경과 합성용")
):
    """
    multipart/form-data로 이미지 생성 요청을 받습니다.
    - prompt: 텍스트 필드
    - product_image: 파일 (선택사항)
    """
    try:
        # product_image가 있으면 바이트로 읽기
        product_image_bytes = None
        if product_image:
            product_image_bytes = await product_image.read()
        
        # 이미지 생성 (product_image_bytes를 서비스에 전달)
        image_bytes = generate_poster_image(prompt, product_image_bytes)
        image_stream = io.BytesIO(image_bytes)
        return StreamingResponse(image_stream, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))