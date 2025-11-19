# router.py

from fastapi import APIRouter
from backend.app.api.routes import whisper, gpt, diffusion, weather, ads, auth, segmentation_test

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(whisper.router)
api_router.include_router(gpt.router)
api_router.include_router(diffusion.router)
api_router.include_router(weather.router)
api_router.include_router(ads.router)
# 제품 이미지 segmentation 테스트
api_router.include_router(segmentation_test.router)