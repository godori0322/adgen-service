"""
env_loader.py
──────────────────────────────────────────────
역할:
 - Hugging Face, Diffusers, FastAPI 환경을 위한 .env 자동 로더
 - find_dotenv()로 현재 디렉터리 기준 상위에서 가장 가까운 .env 탐색
 - 중복 로드 방지 (Uvicorn reload 시에도 안정)
 - HF_TOKEN / HUGGINGFACE_TOKEN / HF_API_KEY 등 여러 키 지원
 - 캐시 경로 자동 생성 (HF_HOME, TRANSFORMERS_CACHE, DIFFUSERS_CACHE)
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# 이미 한 번 로드했는지 여부를 기록하는 플래그 (리로더 환경 대비)
_ENV_LOADED = False


@dataclass(frozen=True)
class Settings:
    hf_token: Optional[str]
    hf_home: str
    transformers_cache: str
    diffusers_cache: str
    model_id: str
    dtype: str
    device_preference: str
    safety_checker: bool


def _ensure_dirs(path: str) -> str:
    """경로가 없으면 폴더를 만들고 그대로 반환"""
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def load_env(force: bool = False) -> None:
    """
    .env 파일을 한 번만 로드.
    - force=True이면 테스트 등에서 재로드 가능
    - find_dotenv(usecwd=True)로 현재 작업경로 기준 탐색
    """
    global _ENV_LOADED
    if _ENV_LOADED and not force:
        return

    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
        print(f"[env_loader] .env loaded from: {dotenv_path}")
    else:
        load_dotenv(override=False)
        print("[env_loader] .env file not found, using environment only")

    _ENV_LOADED = True


def get_settings() -> Settings:
    """로드된 환경변수로부터 Settings 객체를 생성"""
    hf_home = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    transformers_cache = os.getenv("TRANSFORMERS_CACHE", os.path.join(hf_home, "transformers"))
    diffusers_cache = os.getenv("DIFFUSERS_CACHE", os.path.join(hf_home, "diffusers"))

    _ensure_dirs(hf_home)
    _ensure_dirs(transformers_cache)
    _ensure_dirs(diffusers_cache)

    model_id = os.getenv("SD_MODEL_ID", "stabilityai/stable-diffusion-2-1-base")
    dtype = os.getenv("TORCH_DTYPE", "auto").lower()       # auto | fp16 | bf16 | fp32
    device_preference = os.getenv("DEVICE", "auto").lower()  # cuda | mps | cpu | auto
    safety_checker = os.getenv("SAFETY_CHECKER", "true").lower() in {"1", "true", "yes", "on"}

    # 여러 키 이름 지원 (HF_TOKEN / HUGGINGFACE_TOKEN / HF_API_KEY)
    hf_token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
        or os.getenv("HF_API_KEY")
    )

    return Settings(
        hf_token=hf_token,
        hf_home=hf_home,
        transformers_cache=transformers_cache,
        diffusers_cache=diffusers_cache,
        model_id=model_id,
        dtype=dtype,
        device_preference=device_preference,
        safety_checker=safety_checker,
    )


# 모듈이 import될 때 자동으로 .env 로드 (Uvicorn 리로더 시에도 중복 방지)
load_env(force=False)
