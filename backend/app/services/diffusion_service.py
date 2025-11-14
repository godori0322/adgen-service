import threading
import torch
from diffusers import StableDiffusionPipeline
from io import BytesIO

_pipe = None
_pipe_lock = threading.Lock()


def _load_pipeline():
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        use_safetensors=True,
    ).to("cuda")
    pipe.enable_attention_slicing()
    return pipe


def get_pipeline():
    global _pipe
    if _pipe is None:
        with _pipe_lock:
            if _pipe is None:
                _pipe = _load_pipeline()
    return _pipe


def generate_poster_image(prompt: str) -> bytes:
    try:
        prompt = str(prompt).encode("utf-8", errors="ignore").decode("utf-8")

        print(f"[SDXL] generating image for prompt: {prompt}")
        pipe = get_pipeline()
        image = pipe(prompt=prompt, num_inference_steps=30, guidance_scale=7.0).images[0]

        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        raise RuntimeError(f"Diffusion pipeline error: {e}")