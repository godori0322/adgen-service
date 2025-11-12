# ads.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.app.services.whisper_service import transcribe_audio
from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea, extract_city_name_english
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.api.routes.auth import get_current_user
from backend.app.core.models import User
import io
import json

router = APIRouter(prefix="/ads", tags=["Ad Generation"])

@router.post("/generate")
async def generate_ad(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """
    음성 기반 광고 생성 (인증 필요)
    - 사용자의 사업자 정보를 자동으로 context에 포함
    """
    try:
        text = transcribe_audio(file)
        print(f"[음성 변환 결과]: {text}")

        # 한글 지역명을 영어 도시명으로 변환 (GPT 활용)
        city_english = extract_city_name_english(current_user.location or "서울")
        print(f"[지역명 변환]: {current_user.location} -> {city_english}")
        
        # 영어 도시명으로 날씨 조회
        weather_data = get_weather(city_english)
        weather_desc = weather_data["weather"][0]["description"]
        temp = weather_data["main"]["temp"]
        
        # 사용자 메뉴 정보 파싱
        menu_items_str = "정보 없음"
        if current_user.menu_items:
            try:
                menu_list = json.loads(current_user.menu_items)
                menu_items_str = ", ".join(menu_list)
            except:
                menu_items_str = current_user.menu_items
        
        # 사용자 정보를 포함한 context 생성
        context = f"""
업종: {current_user.business_type or '정보 없음'}
위치: {current_user.location or '정보 없음'}
메뉴/서비스: {menu_items_str}
영업시간: {current_user.business_hours or '정보 없음'}
날씨: {weather_desc}, {temp}°C
        """.strip()
        print(f"[컨텍스트 정보]:\n{context}")

        gpt_result = generate_marketing_idea(text, context=context)
        idea = gpt_result.get("idea", "")
        caption = gpt_result.get("caption", "")
        hashtags = gpt_result.get("hashtags", [])
        image_prompt = gpt_result.get("image_prompt", "")

        print(f"[GPT 아이디어] {idea}")
        print(f"[이미지 프롬프트] {image_prompt}")

        image_bytes = generate_poster_image(image_prompt)
        image_stream = io.BytesIO(image_bytes)

        headers = {"X-Generated-Idea": idea}
        return StreamingResponse(image_stream, media_type="image/png", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))