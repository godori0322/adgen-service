# audio.py
# backend/app/routes/audio.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.app.core.schemas import AudioGenerationRequest, AudioGenerationResponse
from backend.app.services.audio_service import generate_bgm_and_save, generate_bgm_bytes


router = APIRouter(
    prefix="/audio",
    tags=["Audio"],
)


@router.post("/generate", response_model=AudioGenerationResponse)
def generate_audio(
    request: AudioGenerationRequest,
    fastapi_request: Request,   # 실제 HTTP 요청 정보(호스트, 포트 등)을 받기
) -> AudioGenerationResponse:
    """
    (기존 방식)
    Replicate MusicGen을 호출해 텍스트 프롬프트 기반 BGM을 생성하고,
    서버 디스크(media/audio)에 저장한 뒤,
    접근 가능한 **절대 URL**을 JSON으로 반환하는 엔드포인트.

    - 사용 예:
      - 기록/히스토리용 BGM
      - 나중에 다시 들을 수 있도록 DB에 audio_url을 저장하고 싶을 때
    """
    try:
        # 파일을 생성하고, "/media/audio/xxxx.wav" 같은 상대 경로를 받기
        relative_audio_path = generate_bgm_and_save(request)
    except Exception as e:
        # 내부 오류를 HTTP 500으로 래핑해서 반환
        raise HTTPException(status_code=500, detail=str(e))

    # base_url : e.g. "http://127.0.0.1:8500"
    base_url = str(fastapi_request.base_url).rstrip("/")    # 끝의 "/" 제거
    # 절대 url 구성 : "http://127.0.0.1:8500" + "/media/audio/xxxx.wav"
    full_audio_url = f"{base_url}{relative_audio_path}"

    # BaseResponse 상속 구조를 유지하면서 AudioGenerationResponse 구성
    return AudioGenerationResponse(
        status="success",
        message="BGM 생성 완료",
        audio_url=full_audio_url,   # 절대 url
        prompt=request.prompt,
        duration_sec=request.duration_sec,
    )


@router.post("/generate/raw")
def generate_audio_raw(
    request: AudioGenerationRequest,
):
    """
    (스트리밍 방식)
    Replicate MusicGen을 호출해 **바이너리 오디오를 바로 스트리밍**으로 내려주는 엔드포인트.

    - JSON 응답이 아니라, Content-Type: audio/wav 로 바로 응답
    - 프론트에서 fetch → blob → URL.createObjectURL → <audio src=...> 로 바로 재생 가능
    - 파일로 남기고 싶지 않고 "바로 듣기"만 하고 싶을 때 사용
    """
    try:
        audio_bytes = generate_bgm_bytes(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # StreamingResponse는 generator나 iterator를 받기 때문에,
    # 간단히 iter([audio_bytes])로 한 번에 내려보내도록 구성
    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/wav",
        headers={
            # inline: 브라우저에서 바로 재생하려고 시도
            "Content-Disposition": 'inline; filename="bgm.wav"',
        },
    )