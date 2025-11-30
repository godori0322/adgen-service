# ads.py

from pathlib import Path
from typing import Optional
from datetime import datetime
import base64
import json

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.services.audio_service import generate_bgm_and_save
from backend.app.services.media_service import (
    save_generated_image,
    compose_image_and_audio_to_mp4
)
from backend.app.core.schemas import GPTRequest, AdGenerateResponse, AudioGenerationRequest
from backend.app.core.database import get_db
from backend.app.core.models import User, AdRequest
from backend.app.services import auth_service



router = APIRouter(prefix="/ads", tags=["Ad Generation"])
security = HTTPBearer(auto_error=False)

@router.post("/generate", response_model=AdGenerateResponse)
async def generate_ad(
    req: GPTRequest, 
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
            weather_info = get_weather(current_user.location or "Seoul")
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
            
            context = f"""
업종: {business_type}
위치: {location}
메뉴/서비스: {menu_items_str}
영업시간: {business_hours}
날씨: {weather_info}
현재 날짜 및 시간: {current_datetime}
            """.strip()
            print(f"[사용자 정보 포함] {current_user.username}")
        else:
            # 비로그인 경우: 기본 정보 및 날짜/시간 제공
            context = f"현재 날짜 및 시간: {current_datetime}"
            print(f"[비로그인 사용자]")

        # GPT 프롬프트 생성 및 실행
        gpt_full_prompt = f"사용자 요청: {req.text}\n\nContext:\n{context}"
        print(f"[GPT 프롬프트]:\n{gpt_full_prompt}")
        
        # ---------------------------------------------------------------
        # 1) GPT: 마케팅 아이디어 + 프롬프트 생성
        # ---------------------------------------------------------------
        print("[ADS] GPT 아이디어 생성 시작")
        gpt_result = await generate_marketing_idea(
            prompt_text=req.text,
            context=context
        )
        idea = gpt_result.get("idea", "")
        caption = gpt_result.get("caption", "")
        hashtags = gpt_result.get("hashtags", [])
        image_prompt = gpt_result.get("image_prompt", "")
        bgm_prompt = gpt_result.get("bgm_prompt", "")

        print(f"[GPT 아이디어] {idea}")
        print(f"[이미지 프롬프트] {image_prompt}")
        print(f"[BGM 프롬프트] {bgm_prompt}")
        print("[ADS] GPT 아이디어 생성 완료")

        # base_url (절대 url 생성용)
        base_url = str(request.base_url).rstrip("/")


        # -------------------------
        # 2) 이미지 생성 (옵션)
        # -------------------------        
        print("[ADS] 이미지 생성 시작")

        image_base64: str = ""
        image_url: Optional[str] = None
        image_path: Optional[Path] = None

        if req.generate_image:
            # 1) 플레이스홀더 이미지 생성 (PNG bytes)
            #    - 나중에 SAM + ControlNet + IP-Adapter로 바꿀 예정
            image_bytes = generate_poster_image(
                prompt=image_prompt,
                product_image_bytes=None,  # 음성만 있는 시나리오라서 일단 None
            )

            # 2) Base64 인코딩 (프론트용)
            image_base64 = base64.b64encode(image_bytes).decode("ascii")

            # 3) 파일 저장 → /media/images/xxxx.png
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
            voice_text=req.text,
            weather_info=weather_info,
            gpt_prompt=gpt_full_prompt,
            gpt_output_text=gpt_output_text,
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