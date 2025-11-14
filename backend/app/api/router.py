# router.py

from fastapi import APIRouter
from backend.app.api.routes import whisper, gpt, diffusion, weather, ads, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(whisper.router)
api_router.include_router(gpt.router)
api_router.include_router(diffusion.router)
api_router.include_router(weather.router)
api_router.include_router(ads.router)