# text.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw
import io
from backend.app.core.database import get_db
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.services.text_service import TextService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.services import auth_service

router = APIRouter(prefix="/text", tags=["Text Overlay"])
security = HTTPBearer(auto_error=False)

text_service = TextService()

# ---------------------------------------------------------
# 텍스트 합성 API
# ---------------------------------------------------------
@router.post("/apply")
async def apply_text(
    image_file: UploadFile = File(...),
    text: str = Form(...),
    mode: str = Form("bottom"),
    font_mode: str = Form("regular"),
    font_size_ratio: float = Form(0.06),
    color_r: int = Form(255),
    color_g: int = Form(255),
    color_b: int = Form(255),
):
    img_bytes = await image_file.read()
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    color = (color_r, color_g, color_b)
    
    image_url = text_service.add_text(
        image=image,
        text=text,
        mode=mode,
        font_mode=font_mode,
        font_size_ratio=font_size_ratio,
        color=color,
        type="final"
    )

    try:
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 텍스트 미리보기 API (Diffusion 없이, 가상 배경 위에 텍스트만 렌더링)
# ---------------------------------------------------------
@router.post("/preview")
async def preview_text(
    text: str = Form(...),
    font_mode: str = Form("regular"),
    mode: str = Form("bottom"),
    color_r: int = Form(255),
    color_g: int = Form(255),
    color_b: int = Form(255),
    width: int = Form(768),
    height: int = Form(1024),
):
    """
    Diffusion 실행 없이 텍스트 스타일 미리보기용 API. (배경 이미지는 단색)
    """
    bg_color = (40, 40, 40)
    bg = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(bg)

    for i in range(height):
        shade = 40 + int(i / height * 40)
        draw.line((0, i, width, i), fill=(shade, shade, shade))

    color = (color_r, color_g, color_b)

    result = text_service.add_text(
        image=bg,
        text=text,
        mode=mode,
        font_mode=font_mode,
        color=color,
        type="preview",
    )

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)

    try:
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 폰트 목록 조회 API
# ---------------------------------------------------------
@router.get("/fonts")
async def get_font_modes():
    return {
        "status": "success",
        "fonts": list(text_service.font_map.keys())
    }