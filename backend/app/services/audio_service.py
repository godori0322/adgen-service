# audio_service.py
# backend/app/services/audio_service.py

import os
from pathlib import Path
from uuid import uuid4

import requests               # 오디오 파일 다운로드용 HTTP 클라이언트
from dotenv import load_dotenv
import replicate              # Replicate MusicGen SDK

from backend.app.core.schemas import AudioGenerationRequest
# AudioGenerationRequest: prompt, duration_sec를 담는 요청 스키마
# prompt : bgm_prompt
# duration_sec : 음원 생성 길이(초 단위)

# 1) .env 파일 로드
load_dotenv()

# 2) 환경변수에서 Replicate 설정 읽기
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
MUSICGEN_MODEL_VERSION = os.getenv("REPLICATE_MUSICGEN_VERSION")

# 3) 오디오 파일 저장 디렉토리
MEDIA_ROOT = Path("media/audio")

def _call_musicgen_via_replicate(prompt: str, duration_sec: float) -> bytes:
    """
    Replicate MusicGen API를 호출해서 오디오 바이너리를 받아오는 함수.

    - 입력:
      - prompt: gpt_service가 생성한 bgm_prompt (영어 MusicGen 설명 문장)
      - duration_sec: 생성하고 싶은 음원의 길이(초)

    - 출력:
      - 생성된 오디오 파일의 raw bytes (wav 데이터)
    """
    if not REPLICATE_API_TOKEN:
        # .env에 REPLICATE_API_TOKEN 이 없을 때 에러
        raise RuntimeError("REPLICATE_API_TOKEN이 설정되어 있지 않습니다. .env를 확인해야 하는 상황")

    # Replicate SDK에 토큰 설정
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

    # duration을 MusicGen이 허용하는 범위로 보정 (예: 1~30초로 클램핑)
    duration = max(1.0, min(float(duration_sec), 30.0))

    try:
        # Replicate prediction 호출
        output = replicate.run(
            MUSICGEN_MODEL_VERSION,
            input={
                "prompt": prompt,
                "duration": duration,
            },  
        )
        # output 타입 정규화:
        # - [FileOutput] 인 경우 → 첫 번째만 사용
        # - FileOutput 인 경우 → 그대로 사용
        # - str(URL) 인 경우 → requests로 다운로드

        file_obj = None

        # 1) 리스트/튜플인 경우
        if isinstance(output, (list, tuple)) and output:
            file_obj = output[0]
        else:
            file_obj = output

        # 2) FileOutput(or 유사 객체) 인 경우: read() 메서드가 있으면 바로 바이너리 추출
        if hasattr(file_obj, "read"):
            try:
                audio_bytes = file_obj.read()
                print(f"[MusicGen] 생성된 오디오 크기: {len(audio_bytes)} bytes")
                return audio_bytes
            except Exception as e:
                raise RuntimeError(f"FileOutput.read() 실패: {e}")

        # 3) 혹시 문자열(URL)인 경우: 요청해서 가져오기
        if isinstance(file_obj, str):
            resp = requests.get(file_obj, stream=True, timeout=120)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"MusicGen 오디오 다운로드 실패: status={resp.status_code}, body={resp.text}"
                )
            return resp.content

        # 4) 여기까지 오면 예기치 못한 타입
        raise RuntimeError(f"예상하지 못한 MusicGen output 타입: {type(file_obj)}")

    except Exception as e:
        # Replicate API 단계에서 실패
        raise RuntimeError(f"Replicate MusicGen API 호출 실패: {e}")


def generate_bgm_and_save(request: AudioGenerationRequest) -> str:
    """
    AudioGenerationRequest를 받아 Replicate MusicGen을 호출하고,
    생성된 오디오를 media/audio 디렉토리에 저장한 뒤
    '상대 경로 URL 문자열'을 반환하는 함수.

    - 예: "/media/audio/xxxx.wav"
    - 이 경로를 FastAPI StaticFiles가 서빙하고,
      라우터에서 base_url과 합쳐서 절대 URL로 만들어 줌.
    """
    # 1) Replicate MusicGen 호출 → 오디오 바이너리 획득
    audio_bytes = _call_musicgen_via_replicate(
        prompt=request.prompt,
        duration_sec=request.duration_sec,
    )

    # 2) media/audio 디렉토리 생성 (없으면 자동 생성)
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    # 3) 파일명 = UUID + .wav (MusicGen 출력은 보통 .wav)
    filename = f"{uuid4().hex}.wav"
    file_path = MEDIA_ROOT / filename

    # 4) 바이너리 저장
    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    # 5) StaticFiles 기준으로 접근 가능한 URL 구성
    #    (router에서 base_url을 붙여 절대 경로로 변환)
    audio_url = f"/media/audio/{filename}"

    return audio_url


def generate_bgm_bytes(request: AudioGenerationRequest) -> bytes:
    """
    프론트에서 바로 재생할 수 있도록
    파일로 저장하지 않고 **오디오 raw bytes만** 반환하는 함수.

    - 스트리밍 응답(StreamingResponse)에서 그대로 사용.
    - 파일을 디스크에 남기고 싶지 않은 "체험용" 용도에 적합.
    """
    audio_bytes = _call_musicgen_via_replicate(
        prompt=request.prompt,
        duration_sec=request.duration_sec,
    )
    return audio_bytes