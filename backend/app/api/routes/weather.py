# weather.py

from fastapi import APIRouter, Query, HTTPException
from backend.app.services.weather_service import get_weather
from backend.app.core.schemas import WeatherResponse

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/", response_model=WeatherResponse)
async def weather(city: str = Query("Seoul", description="도시 이름")):
    try:
        data = await get_weather(city)
        return WeatherResponse(
            city=city,
            temp=data["main"]["temp"],
            desc=data["weather"][0]["description"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
