# whisper_service.py
# Whisper API를 이용해 사용자 입력 음성을 텍스트로 변환

import httpx
import os
from fastapi import UploadFile

async def transcribe_audio(file: UploadFile) -> str:
    """
    [비동기] Whisper API로 음성을 텍스트로 변환
    
    ⚠️ 중요: Whisper는 파일 업로드 + 처리 시간이 길어서 (5-15초)
             비동기 처리가 필수입니다!
    """
    try:
        # 파일 내용 읽기
        file_content = await file.read()
        
        # httpx.AsyncClient로 비동기 요청
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
                files={"file": (file.filename, file_content, file.content_type or "audio/mpeg")},
                data={"model": "whisper-1", "language": "ko"}
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Whisper API Error: {response.text}")
            
            return response.json()["text"]
    
    except Exception as e:
        raise RuntimeError(f"Whisper API Error: {e}")
    finally:
        # 파일 포인터 리셋
        await file.seek(0)