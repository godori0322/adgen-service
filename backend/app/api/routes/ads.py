# ads.py

from pathlib import Path
from typing import Optional
from datetime import datetime
import base64
import json

from backend.app.core.schemas import (
    AdMediaGenerateRequest,
    AdGenerateResponse,
    AudioGenerationRequest,
    CompositionMode,
)
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
    Depends,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.services.weather_service import get_weather
from backend.app.services.diffusion_service import (
    generate_poster_image,
    generate_poster_with_product_b64
)
from backend.app.services.audio_service import generate_bgm_and_save
from backend.app.services.media_service import (
    save_generated_image,
    compose_image_and_audio_to_mp4,
    overlay_caption_on_image,   # 텍스트 삽입 추가
)
from backend.app.core.schemas import (
    AdMediaGenerateRequest,   # 새로 만든 Request 스키마
    AdGenerateResponse,       # 기존 Response 그대로 사용
    AudioGenerationRequest,
)
from backend.app.core.schemas import (
    AdMediaGenerateRequest,
    AdGenerateResponse,
    AudioGenerationRequest,
    CompositionMode,
)
from backend.app.core.database import get_db
from backend.app.core.models import User, AdRequest
from backend.app.services import auth_service



router = APIRouter(prefix="/ads", tags=["Ad Generation"])
security = HTTPBearer(auto_error=False)

@router.post("/generate/upload", response_model=AdGenerateResponse)
async def generate_ad_upload(
    request: Request,
    # 파일 업로드
    product_image: UploadFile = File(
        ...,
        description="제품 이미지 파일 (PNG/JPEG)",
    ),
    # 텍스트 관련 폼 필드
    idea: Optional[str] = Form(
        None,
        description="GPT가 생성한 광고 아이디어 문장",
    ),
    caption: Optional[str] = Form(
        None,
        description="SNS/포스터에 들어갈 메인 카피 문장",
    ),
    hashtags: Optional[str] = Form(
        None,
        description="쉼표(,)로 구분된 해시태그 문자열 예: #브런치,#서울카페,#주말특별",
    ),
    image_prompt: str = Form(
        ...,
        description="이미지 생성용 프롬프트 (예: A cozy cafe setting ...)",
    ),
    bgm_prompt: Optional[str] = Form(
        None,
        description="BGM 생성용 프롬프트",
    ),
    composition_mode: CompositionMode = Form(
        CompositionMode.balanced,
        description="합성 모드 (rigid/balanced/creative)",
    ),
    generate_image: bool = Form(
        True,
        description="이미지 생성 여부 플래그",
    ),
    generate_audio: bool = Form(
        False,
        description="BGM 생성 여부 플래그",
    ),
    generate_video: bool = Form(
        False,
        description="이미지 + 오디오 mp4 합성 여부 플래그",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Swagger/테스트용 파일 업로드 버전 광고 생성 엔드포인트 정의.
    - product_image: 파일 업로드
    - 나머지 필드: form-data 텍스트 필드
    - 내부에서 AdMediaGenerateRequest로 변환 후 기존 generate_ad 재사용
    """
    try:
        # 1) 업로드 이미지 → bytes
        product_bytes = await product_image.read()

        # 2) bytes → Base64 문자열
        product_image_b64 = base64.b64encode(product_bytes).decode("ascii")

        # 3) 해시태그 문자열 → 리스트 변환
        if hashtags:
            hashtags_list = [
                h.strip()
                for h in hashtags.split(",")
                if h.strip()
            ]
        else:
            hashtags_list = []

        # 4) 기존 JSON 스키마로 래핑
        ad_req = AdMediaGenerateRequest(
            idea=idea,
            caption=caption,
            hashtags=hashtags_list,
            image_prompt=image_prompt,
            bgm_prompt=bgm_prompt,
            product_image_b64=product_image_b64,
            composition_mode=composition_mode,
            generate_image=generate_image,
            generate_audio=generate_audio,
            generate_video=generate_video,
        )

        # 5) 기존 generate_ad 로직 재사용
        return await generate_ad(
            req=ad_req,
            request=request,
            credentials=credentials,
            db=db,
        )
    except HTTPException:
        # generate_ad 내부에서 일어난 HTTPException 그대로 전달
        raise
    except Exception as e:
        db.rollback()
        print(f"[ADS][UPLOAD][ERROR] {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/generate", response_model=AdGenerateResponse)
async def generate_ad(
    req: AdMediaGenerateRequest, 
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    print("[ADS] /api/ads/generate called")

    """
    광고 생성 API
    - 로그인 시: 사용자 정보 활용 및 DB에 요청 기록 저장
    - 비로그인 시: 기본 정보로 광고 생성, DB에는 user_id=NULL로 저장

    옵션 플래그:
    - generate_image: 이미지만 생성
    - generate_audio: BGM 생성
    - generate_video: 이미지 + 오디오 mp4 합성
    """
    try:
        # 0-0) base_url 계산
        base_url = str(request.base_url).rstrip("/")

        # ---------------------------------------------------------------
        # 0) 로그인/비로그인 분기 + 컨텍스트 구성
        # ---------------------------------------------------------------
        # 토큰에서 사용자 정보 추출 (optional)
        token = credentials.credentials if credentials else None
        current_user = auth_service.get_user_from_token(db, token)
        
        # 현재 날짜 및 시간 정보 가져오기
        current_datetime = datetime.now().strftime("%Y년 %m월 %d일 %H시")
        # Context 생성 (로그인 여부에 따라 다름)
        weather_info = None  # 기본값 설정

        if current_user:
            # 로그인한 경우: 사용자 정보 활용
            weather_info = await get_weather(current_user.location or "Seoul")
            business_type = current_user.business_type or "정보 없음"
            location = current_user.location or "정보 없음"
            business_hours = current_user.business_hours or "정보 없음"

            menu_items_str = "정보 없음"
            if current_user.menu_items:
                try:
                    menu_list = json.loads(current_user.menu_items)
                    menu_items_str = ", ".join(menu_list)
                except:
                    menu_items_str = current_user.menu_items

            # context는 이제 "GPT용"이 아니라 "로그용"으로만 사용
            context_str = (
                f"업종: {business_type}, 위치: {location}, 영업시간: {business_hours}, 메뉴: {menu_items_str}"
            )
            print(f"[사용자 정보 포함] {current_user.username}")
        else:
            context_str = f"현재 날짜 및 시간: {current_datetime}"
            print("[비로그인 사용자]")

        # ---------------------------------------------------------------
        # 1) GPT 결과값은 프론트에서 받은 것을 그대로 사용
        # ---------------------------------------------------------------
        idea = req.idea or ""
        caption = req.caption or ""
        hashtags = req.hashtags or []
        image_prompt = req.image_prompt or ""
        bgm_prompt = req.bgm_prompt or ""

        # 최소한 image_prompt는 있어야 의미가 있음
        if req.generate_image and not image_prompt:
            raise HTTPException(
                status_code=400,
                detail="generate_image=true 인 경우 image_prompt는 필수입니다.",
            )

        if req.generate_audio and not bgm_prompt:
            raise HTTPException(
                status_code=400,
                detail="generate_audio=true 인 경우 bgm_prompt는 필수입니다.",
            )

        print(f"[GPT 아이디어(프론트 전달)] {idea}")
        print(f"[이미지 프롬프트(프론트 전달)] {image_prompt}")
        print(f"[BGM 프롬프트(프론트 전달)] {bgm_prompt}")

        # -------------------------
        # 2) 이미지 생성 (옵션)
        # -------------------------        
        print("[ADS] 이미지 생성 시작")

        image_base64: str = ""
        image_url: Optional[str] = None
        image_path: Optional[Path] = None

        if req.generate_image:
            if not image_prompt:
                raise HTTPException(
                    status_code=400,
                    detail="generate_image=true 인 경우 image_prompt는 필수입니다.",
                )
            if not req.product_image_b64:
                raise HTTPException(
                    status_code=400,
                    detail="generate_image=true 인 경우 product_image_b64는 필수입니다.",
                )

            print("[ADS] 제품 이미지 기반 합성 포스터 생성 모드 진입")

            # diffusion 파이프라인 전체 호출 (Base64 → 세그멘테이션 → 합성)
            # diffusion으로 제품+배경 합성 이미지 생성
            image_bytes = generate_poster_with_product_b64(
                prompt=image_prompt,
                product_image_b64=req.product_image_b64,
                composition_mode=req.composition_mode,
                control_weight=None,
                ip_adapter_scale=None,
            )

            # caption이 있으면 텍스트 합성
            if req.caption:
                print(f"[ADS] 캡션 텍스트 오버레이 적용: {req.caption}")
                image_bytes = overlay_caption_on_image(
                    image_bytes=image_bytes,
                    caption=req.caption,
                    mode="bottom",      # 디폴트 : 하단
                    font_mode="bold",   # 디폴트 : 볼드
                    font_size_ratio=0.06,
                    color=(255, 255, 255)
                )
            else:
                print("[ADS] 캡션 없음 -> 텍스트 합성 스킵")

            # 텍스트 포함된 이미지 -> base64/파일로 저장
            image_base64 = base64.b64encode(image_bytes).decode("ascii")

            image_path = save_generated_image(image_bytes, ext="png")
            image_url = f"{base_url}/media/images/{image_path.name}"

            print(f"[이미지 생성/저장 완료] {image_path}")
        else:
            print("[옵션] 이미지 생성 비활성화 상태")


        # -------------------------
        # 3) 오디오 생성 (옵션)
        # -------------------------
        audio_url: Optional[str] = None
        audio_file_path: Optional[Path] = None

        if req.generate_audio:
            audio_req = AudioGenerationRequest(
                prompt=bgm_prompt,
                duration_sec=12.0,  # PoC에서 고정 길이
            )
            # "/media/audio/xxxx.wav" 형태의 상대 경로
            relative_audio_path = generate_bgm_and_save(audio_req)

            audio_url = f"{base_url}{relative_audio_path}"
            # 실제 파일 경로 (mp4 합성용)
            audio_file_path = Path("media/audio") / Path(relative_audio_path).name

            print(f"[BGM 생성/저장 완료] {audio_file_path}")
        else:
            print("[옵션] 오디오 생성 비활성화 상태")

        # -------------------------
        # 4) mp4 합성 (옵션)
        # -------------------------
        print("[ADS] 미디어 합성 시작")
        video_url: Optional[str] = None

        if req.generate_video:
            # mp4는 이미지 + 오디오가 모두 있을 때만 의미 있음
            if not (image_path and audio_file_path):
                print("[mp4 합성 스킵] image_path 또는 audio_file_path 없음")
            else:
                try:
                    video_path = compose_image_and_audio_to_mp4(
                        image_path=image_path,
                        audio_path=audio_file_path,
                    )
                    video_url = f"{base_url}/media/video/{video_path.name}"
                    print(f"[mp4 합성 완료] {video_path}")
                except Exception as e:
                    print(f"[mp4 합성 실패] {e}")
        else:
            print("[옵션] mp4 합성 비활성화 상태")

        # -------------------------
        # 5) DB 저장 (로그인/비로그인 공통)
        # -------------------------
        # GPT 출력 텍스트 생성
        gpt_output_text = f"아이디어: {idea}\n캡션: {caption}\n해시태그: {', '.join(hashtags)}"

        # DB에 광고 요청 정보 저장
        ad_request = AdRequest(
            user_id=current_user.id if current_user else None,
            voice_text=None,
            weather_info=weather_info,
            gpt_prompt=context_str,          # full 프롬프트 대신 context 요약 정도
            gpt_output_text=gpt_output_text, # GPT 결과 요약 문자열
            diffusion_prompt=image_prompt,
            image_url=image_url,
            audio_url=audio_url,
            video_url=video_url,
            hashtags=json.dumps(hashtags, ensure_ascii=False),
        )
        db.add(ad_request)
        db.commit()
        db.refresh(ad_request)
        print(f"[DB 저장 완료] AdRequest ID: {ad_request.id}")

        # -------------------------
        # 6) 최종 응답
        # -------------------------
        return AdGenerateResponse(
            idea=idea,
            caption=caption,
            hashtags=hashtags,
            image_prompt=image_prompt,
            image_base64=image_base64,  # generate_image=False면 빈 문자열
            image_url=image_url,
            audio_url=audio_url,
            video_url=video_url,
        )

    except Exception as e:
        db.rollback()
        print(f"[ADS][ERROR] {repr(e)}")  # ← 에러 내용 콘솔에 찍기
        raise HTTPException(status_code=500, detail=str(e))