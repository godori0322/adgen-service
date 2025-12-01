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
from fastapi.staticfiles import StaticFiles 
from backend.app.api.router import api_router
from backend.app.core.database import engine, Base
from backend.app.core.minio_client import minio_client, BUCKET_IMAGE, BUCKET_VIDEO, BUCKET_AUDIO

            
# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice2Marketing API Prototype")

@app.on_event("startup")
async def startup_event():
    # FastAPI 시작 시 버킷 존재 여부 확인 + 생성
    for bucket in [BUCKET_IMAGE, BUCKET_VIDEO, BUCKET_AUDIO]:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
            print(f"📦 Bucket created: {bucket}")
        else:
            print(f"📦 Bucket exists: {bucket}")

# media 디렉토리 정적 서빙
app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media",
)


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
