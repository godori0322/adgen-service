# main.py
# fastapi 애플리케이션 엔트리포인트 구성
# 공통 미들웨어 설정 및 API 라우터 등록
# 헬스체크용 루트 엔드포인트 제공

from .env_loader import load_env, get_settings   # 상대 경로 주의
load_env()
SETTINGS = get_settings()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router

app = FastAPI(title="Voice2Marketing API Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Voice2Marketing API is running"}
