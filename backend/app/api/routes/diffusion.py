# diffusion.py

from math import e
from fastapi import APIRouter, HTTPException
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.core.schemas import DiffusionRequest, DiffusionResponse
import base64

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

@router.post("/generate", response_model=DiffusionResponse)
async def generate_image(req: DiffusionRequest):
    try:
        image_bytes = generate_poster_image(req.prompt)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"
        return DiffusionResponse(image_url=image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
