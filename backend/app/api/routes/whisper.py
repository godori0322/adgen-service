# whisper.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.whisper_service import transcribe_audio
from backend.app.core.schemas import WhisperResponse

router = APIRouter(prefix="/whisper", tags=["Whisper"])

@router.post("/transcribe", response_model=WhisperResponse)
async def transcribe(file: UploadFile = File(...)):
    try:
        text = transcribe_audio(file)
        return WhisperResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
