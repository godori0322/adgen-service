# api 프롬프트 조정 버전
# # whisper_service.py 
# # WAV 파일을 메모리에 읽어 API로 전송하는 안전성 강화 버전


import requests
import os
import io # io 모듈 추가
from fastapi import UploadFile

def transcribe_audio(file: UploadFile) -> str:
    # 1. 파일 내용을 메모리에 모두 읽기(가장 확실한 방법)
    #    async/sync 환경에서 파일 포인터 충돌을 방지
    file_content = file.file.read() 
    
    # 2. WAV 파일에 맞춰 MIME 타입을 "audio/wav"로 지정
    mime_type = "audio/wav" 
    
    # 3. 메모리 바이트를 requests가 사용할 수 있도록 io.BytesIO로 감싼다
    files = {
        "file": (
            file.filename, 
            io.BytesIO(file_content), # 메모리에서 읽은 바이트 사용
            mime_type
        )
    }
    
    # 튜닝 최적화 : language ,prompt 매개변수 추가
    data_form = {
        "model": "whisper-1",
        "language": "ko",  # 한국어로 명시
        # 자주 사용하는 고유 명사, 전문 용어 추가"
        "prompt": "타겟 고객 연령, 타겟 고객 특징, 운영하는 가게의 업종, 가게의 분위기, 가게의 위치, 가게의 이름, 상권 특징에 대해서 말해주세요."
    }


    response = requests.post(
        "https://api.openai.com/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
        files=files,
        data=data_form
    )
    
    if response.status_code != 200:
        # 파일이 유효하다면 이 에러가 발생하지 않아야 함
        raise RuntimeError(f"Whisper API Error: {response.text}")
        
    return response.json()["text"]

#----------------------------------------------------------------------------
# whisper_service.py
# Whisper API 업로드 전에 어떤 입력 포맷이든 16kHz/mono/PCM WAV로 강제 변환
# ffmpeg/ffprobe로 파일 유효성 검사 및 변환 실패 방어 --> 다만 변환된 오디오 파일이 너무 짧아 오류가 계속발생
    # 사용하지 않기로 결정

# import os
# import io
# import mimetypes
# import shutil # ffmpeg, ffprobe 존재 확인용
# import subprocess # ffmpeg/ffprobe 파이프 실행용
# import requests
# from fastapi import UploadFile
# import json # JSON 파싱을 위해 추가

# # 서버에서 허용할 확장자 목록
# SUPPORTED_EXTS = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".oga", ".ogg", ".wav", ".webm"}

# # 최소 파일 크기 검사 (변환 실패 방어)
# MIN_WAV_SIZE = 4096 

# def _ensure_ffmpeg():
#     """ffmpeg 실행파일이 PATH에 있는지 확인."""
#     if shutil.which("ffmpeg") is None:
#         raise RuntimeError("ffmpeg가 설치되어 있지 않습니다. 서버에 ffmpeg를 설치해 주세요.")

# def _ensure_ffprobe():
#     """ffprobe 실행파일이 PATH에 있는지 확인."""
#     if shutil.which("ffprobe") is None:
#         raise RuntimeError("ffprobe가 설치되어 있지 않습니다. 서버에 ffprobe를 설치해 주세요.")

# def _ffprobe_check_duration(in_bytes: bytes) -> None:
#     """오디오 바이트를 ffprobe로 검사하여 길이가 0.1초 미만인지, 유효한 파일인지 확인."""
#     _ensure_ffprobe()
    
#     cmd = [
#         "ffprobe",
#         "-v", "error", 
#         "-show_entries", "format=duration",
#         "-of", "json",
#         "-i", "pipe:0",
#     ]

#     proc = subprocess.run(
#         cmd,
#         input=in_bytes,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         check=False,
#     )
    
#     if proc.returncode != 0:
#         raise ValueError(
#             f"오디오 파일 분석 실패 (ffprobe): {proc.stderr.decode(errors='ignore')}. "
#             "원본 오디오 파일이 유효한 형식인지, 오디오 데이터가 있는지 확인하세요."
#         )

#     try:
#         data = json.loads(proc.stdout)
#         duration = float(data.get("format", {}).get("duration", 0.0))
        
#         if duration < 0.1:
#             raise ValueError(
#                 f"오디오 파일 길이: {duration:.2f}초. Whisper API 최소 요구 길이인 0.1초 미만입니다."
#             )
            
#     except Exception:
#         raise ValueError("오디오 파일에서 유효한 길이 정보를 읽을 수 없습니다. 파일이 손상되었을 수 있습니다.")


# def _bytes_to_wav_pcm16(in_bytes: bytes) -> bytes:
#     """임의의 입력 오디오 바이트를 ffmpeg 파이프를 통해 16kHz / mono / PCM s16le WAV 바이트로 변환."""
#     _ensure_ffmpeg()

#     cmd = [
#         "ffmpeg",
#         "-hide_banner",
#         "-loglevel", "error", 
#         "-i", "pipe:0", 
#         "-ac", "1",
#         "-ar", "16000",
#         "-f", "wav",
#         "-acodec", "pcm_s16le",
#         "pipe:1",
#     ]

#     proc = subprocess.run(
#         cmd,
#         input=in_bytes,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         check=False,
#     )
#     if proc.returncode != 0 or not proc.stdout: 
#         raise RuntimeError(
#             f"오디오 WAV 변환 실패! (크기: {len(proc.stdout)}). "
#             f"FFmpeg 에러: {proc.stderr.decode(errors='ignore')}"
#         )

#     return proc.stdout 

# def transcribe_audio(file: UploadFile) -> str:
#     # 0) 파일명/확장자 검증
#     name = (file.filename or "").strip()
#     _, ext = os.path.splitext(name)
#     ext = ext.lower()
#     if ext not in SUPPORTED_EXTS:
#         raise ValueError(f"지원되지 않는 파일 형식: {ext}")

#     # 1) 파일을 '바이트'로 확보
#     try:
#         file.file.seek(0)
#     except Exception:
#         pass
#     in_bytes = file.file.read()
#     if not in_bytes or len(in_bytes) < 1024: 
#         raise ValueError("Empty or too small audio file")

#     # 1.5) ffprobe를 이용해 길이 사전 검사 (파일 유효성 검증)
#     _ffprobe_check_duration(in_bytes) 
    
#     # 2) 16kHz/mono/PCM WAV로 변환 및 변환 결과 크기 검사
#     try:
#         wav_bytes = _bytes_to_wav_pcm16(in_bytes) 
#     except RuntimeError as e:
#         raise RuntimeError(f"오디오 파일 변환 실패: {e}")
    
#     # 변환된 파일의 크기가 너무 작으면 에러 (FFmpeg 실패 방어용)
#     if len(wav_bytes) < MIN_WAV_SIZE:
#         raise ValueError(f"변환된 오디오 파일이 너무 짧습니다. (크기: {len(wav_bytes)} bytes). 원본 파일에 유효한 오디오 데이터가 있는지 확인하세요.")

#     # 3) OpenAI API 키 확인
#     api_key = os.getenv("OPENAI_API_KEY")
#     if not api_key:
#         raise RuntimeError("OPENAI_API_KEY 미설정(.env 확인)")

#     # 4) 요청: WAV 바이트 업로드
#     safe_name = os.path.splitext(name)[0] + "_16k_mono.wav"
#     files = {"file": (safe_name, io.BytesIO(wav_bytes), "audio/wav")}
#     data_form = {"model": "whisper-1"} 

#     resp = requests.post(
#         "https://api.openai.com/v1/audio/transcriptions",
#         headers={"Authorization": f"Bearer {api_key}"},
#         files=files,
#         data=data_form,
#         timeout=60,
#     )

#     if resp.status_code != 200:
#         raise RuntimeError(f"Whisper API Error {resp.status_code}: {resp.text}")

#     payload = resp.json()
#     return payload.get("text", "")


