# whisper_service.py
# Whisper API를 이용해 사용자 입력 음성을 텍스트로 변환

import requests
import os
from fastapi import UploadFile

def transcribe_audio(file: UploadFile) -> str:
    response = requests.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
        files={"file": (file.filename, file.file, "audio/mpeg")},
        data={"model": "whisper-1"}
    )
    return response.json()["text"]