# diffusion.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.core.schemas import DiffusionRequest
import io

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

@router.post("/generate")
async def generate_image(req: DiffusionRequest):
    try:
        image_bytes = generate_poster_image(req.prompt)
        image_stream = io.BytesIO(image_bytes)
        return StreamingResponse(image_stream, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))