# weather_service.py

from backend.app.services import gpt_service
import requests
import os

async def get_weather(city="Seoul"):
    city = await gpt_service.extract_city_name_english(city)
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": os.getenv("WEATHER_API_KEY"), "lang": "kr", "units": "metric"}
    weather_data = requests.get(url, params=params).json()
    weather_desc = weather_data["weather"][0]["description"]
    temp = weather_data["main"]["temp"]
    weather_info = f"{city}, {weather_desc}, {temp}°C"
    return weather_info