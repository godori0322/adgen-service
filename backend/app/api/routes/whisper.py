# whisper.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.services.whisper_service import transcribe_audio
from backend.app.core.schemas import WhisperResponse

router = APIRouter(prefix="/whisper", tags=["Whisper"])

@router.post("/transcribe", response_model=WhisperResponse)
async def transcribe(file: UploadFile = File(...)):
    """
    [비동기] 음성 파일을 텍스트로 변환
    
    - 파일 업로드 + Whisper API 처리 (5-15초)
    - 비동기 처리로 동시 요청 가능
    """
    try:
        text = await transcribe_audio(file)
        return WhisperResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
