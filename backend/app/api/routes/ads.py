# ads.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.services.diffusion_service import synthesize_image
from backend.app.services.audio_service import generate_bgm_and_save
from backend.app.core.schemas import GPTRequest, AdGenerateResponse, AudioGenerationRequest
from backend.app.core.database import get_db
from backend.app.core.models import User, AdRequest
from backend.app.services import auth_service
from typing import Optional
from datetime import datetime
import base64
import json

router = APIRouter(prefix="/ads", tags=["Ad Generation"])
security = HTTPBearer(auto_error=False)

@router.post("/generate", response_model=AdGenerateResponse)
async def generate_ad(
    req: GPTRequest, 
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    광고 생성 API
    - 로그인 시: 사용자 정보 활용 및 DB에 요청 기록 저장
    - 비로그인 시: 기본 정보로 광고 생성, DB에는 user_id=NULL로 저장
    """
    try:
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
        
        gpt_result = generate_marketing_idea(
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

        # 1) 이미지 생성
        image_bytes = synthesize_image(image_prompt)
        image_base64 = base64.b64encode(image_bytes).decode("ascii")

        # 2) BGM 생성 (replicate musicgen) : AudioGenerationRequest에 bgm_prompt 그대로 넣어줌
        audio_req = AudioGenerationRequest(
            prompt=bgm_prompt,
            duration_sec=12.0,  # 12.0초로 고정
        )
        relative_audio_path = generate_bgm_and_save(audio_req)

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
            image_url=None,  # 현재는 base64로 반환, 추후 S3 업로드 시 URL 저장
            hashtags=json.dumps(hashtags, ensure_ascii=False)
        )
        db.add(ad_request)
        db.commit()
        db.refresh(ad_request)
        print(f"[DB 저장 완료] AdRequest ID: {ad_request.id}")

        return AdGenerateResponse(
            idea=idea,
            caption=caption,
            hashtags=hashtags,
            image_prompt=image_prompt,
            image_base64=image_base64,
            audio_url=full_audio_url,   # 절대 bgm url
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
