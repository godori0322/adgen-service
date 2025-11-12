# # diffusion_service.py
# # 입력받은 프롬프트를 바탕으로 홍보용 이미지 출력

# import os
# import requests

# def generate_poster_image(prompt: str):
#     payload = {"inputs": prompt}
#     response = requests.post(
#         "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2",
#         headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
#         json=payload
#     )
#     if response.status_code != 200:
#         raise RuntimeError(f"Diffusion API Error: {response.text}")
#     return response.content


#-----------------------------------------------------------------------
# diffusion_service.py

import os
import requests

HF_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2"

def generate_poster_image(prompt: str) -> bytes:
    # 0) 입력 검증 역할
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt 누락 또는 공백")

    # 1) 키 확인 역할
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise RuntimeError("HF_API_KEY 미설정")

    # 2) 요청 전송 역할
    try:
        response = requests.post(
            HF_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "image/png",  # 바이너리 이미지 기대 명시 역할
            },
            json={"inputs": prompt.strip()},
            timeout=(5, 60),  # connect/read 타임아웃 역할
        )
    except requests.RequestException as e:
        # 네트워크/타임아웃 등 요청 자체 실패 역할
        raise RuntimeError(f"Diffusion 요청 실패: {e}")

    # 3) 상태 코드 검사 및 오류 본문 전달 역할
    if response.status_code != 200:
        # HF 라우터는 4xx/5xx 시 text/json 본문 제공 → 디버깅 가시성 확보 역할
        raise RuntimeError(f"Diffusion API Error {response.status_code}: {response.text[:500]}")

    # 4) 정상 바이너리 반환 역할
    return response.content
