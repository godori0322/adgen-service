# diffusion_service.py
# 입력받은 프롬프트를 바탕으로 홍보용 이미지 출력

import os
import requests

def generate_poster_image(prompt: str):
    payload = {"inputs": prompt}
    response = requests.post(
        "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2",
        headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
        json=payload
    )
    if response.status_code != 200:
        raise RuntimeError(f"Diffusion API Error: {response.text}")
    return response.content
