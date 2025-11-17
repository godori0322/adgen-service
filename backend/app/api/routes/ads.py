# ads.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.core.schemas import GPTRequest, AdGenerateResponse
from backend.app.core.database import get_db
from backend.app.core.models import User, AdRequest
from backend.app.services import auth_service
from typing import Optional
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
            """.strip()
            print(f"[사용자 정보 포함] {current_user.username}")
        else:
            # 비로그인 경우: 기본 정보만 사용
            context = None
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

        print(f"[GPT 아이디어] {idea}")
        print(f"[이미지 프롬프트] {image_prompt}")

        image_bytes = generate_poster_image(image_prompt)
        image_base64 = base64.b64encode(image_bytes).decode("ascii")

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
            image_base64=image_base64
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
