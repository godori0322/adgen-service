# diffusion_service.py
# 입력받은 프롬프트를 바탕으로 홍보용 이미지 출력

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline
from io import BytesIO

# ✅ 모델 로드 (최초 1회만)
pipe = StableDiffusionXLPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")

pipe.enable_attention_slicing()
pipe.enable_xformers_memory_efficient_attention()

def generate_poster_image(prompt: str) -> bytes:
    print(f"[SDXL] generating image for prompt: {prompt}")
    image = pipe(prompt=prompt,
                 num_inference_steps=30,
                 guidance_scale=7.0
                 ).images[0]
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()