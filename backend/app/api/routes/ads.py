# ads.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.services.whisper_service import transcribe_audio
from backend.app.services.weather_service import get_weather
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.services.diffusion_service import generate_poster_image
import base64
import io

router = APIRouter(prefix="/ads", tags=["Ad Generation"])

@router.post("/generate")
async def generate_ad(file: UploadFile = File(...), city: str = "Seoul"):
    try:
        text = transcribe_audio(file)
        print(f"[음성 변환 결과]: {text}")

        weather_data = get_weather(city)
        weather_desc = weather_data["weather"][0]["description"]
        temp = weather_data["main"]["temp"]
        context = f"{city}, {weather_desc}, {temp}°C"
        print(f"[날씨 정보]: {context}")

        gpt_result = generate_marketing_idea(text, context=context)
        idea = gpt_result.get("idea", "")
        caption = gpt_result.get("caption", "")
        hashtags = gpt_result.get("hashtags", [])
        image_prompt = gpt_result.get("image_prompt", "")

        print(f"[GPT 아이디어] {idea}")
        print(f"[이미지 프롬프트] {image_prompt}")

        image_bytes = generate_poster_image(image_prompt)
        image_stream = io.BytesIO(image_bytes)

        # HTTP headers must be latin-1 compatible, so we base64 encode to avoid
        # errors when the idea contains Korean or other unicode characters.
        encoded_idea = base64.b64encode(idea.encode("utf-8")).decode("ascii")
        headers = {"X-Generated-Idea": encoded_idea}
        return StreamingResponse(image_stream, media_type="image/png", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
