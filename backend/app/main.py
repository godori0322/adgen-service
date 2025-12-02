# main.py

# 캐시파일 /home/shared/models 하위로 설정
import os
# cold start 방지 위해 서버 실행 시 SAM, Diffusion 모델 로드
from backend.app.services.segmentation import get_segmentation_singleton
from backend.app.services.diffusion_service import _load_pipeline
import asyncio
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

    # -----------------------------
    # SAM + Diffusion Preload 추가
    # -----------------------------
    print("🚀 [Startup] Preloading SAM + Diffusion models...")

    # SAM 모델 미리 로드 (GPU 상주)
    try:
        await asyncio.to_thread(lambda: get_segmentation_singleton())
        print("🧩 [Startup] SAM model loaded.")
    except Exception as e:
        print(f"❌ [Startup] SAM preload failed: {e}")

    # Diffusion 파이프라인 미리 로드
    try:
        await asyncio.to_thread(_load_pipeline)
        print("🎨 [Startup] Diffusion pipeline loaded.")
    except Exception as e:
        print(f"❌ [Startup] Diffusion preload failed: {e}")

    print("✨ [Startup] All models ready.")

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
