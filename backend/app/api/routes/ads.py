# ads.py

from fastapi import APIRouter, HTTPException
from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.services.diffusion_service import generate_poster_image
from backend.app.core.schemas import GPTRequest, AdGenerateResponse
import base64

router = APIRouter(prefix="/ads", tags=["Ad Generation"])

@router.post("/generate", response_model=AdGenerateResponse)
async def generate_ad(req: GPTRequest, city: str = "Seoul"):
    try:
        """
        text = transcribe_audio(file)
        print(f"[음성 변환 결과]: {text}")
        """
        weather_data = get_weather(city)
        weather_desc = weather_data["weather"][0]["description"]
        temp = weather_data["main"]["temp"]
        context = f"{city}, {weather_desc}, {temp}°C"
        print(f"[날씨 정보]: {context}")

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

        return AdGenerateResponse(
            idea=idea,
            caption=caption,
            hashtags=hashtags,
            image_prompt=image_prompt,
            image_base64=image_base64
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
