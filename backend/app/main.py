# main.py

# 캐시파일 /home/shared/models 하위로 설정
import os
# Hugging Face / Diffusers / Transformers 캐시를 공용 디렉토리로 지정
CACHE_DIR = "/home/shared/models"
for key in [
            "HF_HOME","TRANSFORMERS_CACHE",
            "DIFFUSERS_CACHE", "HUGGINGFACE_HUB_CACHE", "TORCH_HOME"]:
    os.environ[key] = CACHE_DIR


# .env 로드(기존코드 동일)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
from backend.app.core.database import engine, Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

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
    return {"message": "Voice2Marketing API is running 🚀"}
