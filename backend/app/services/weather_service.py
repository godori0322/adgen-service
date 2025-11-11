# weather_service.py

import requests
import os

def get_weather(city="Seoul"):
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": os.getenv("WEATHER_API_KEY"), "lang": "kr", "units": "metric"}
    res = requests.get(url, params=params)
    return res.json()