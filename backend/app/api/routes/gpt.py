# gpt.py

from fastapi import APIRouter, HTTPException
from backend.app.services.gpt_service import generate_marketing_idea
from backend.app.core.schemas import GPTRequest, GPTResponse

router = APIRouter(prefix="/gpt", tags=["GPT"])

@router.post("/generate", response_model=GPTResponse)
async def generate_marketing_content(req: GPTRequest):
    try:
        result = generate_marketing_idea(
            prompt_text=req.text,
            context=req.context
        )
        return GPTResponse(
            idea=result["idea"],
            caption=result["caption"],
            hashtags=result["hashtags"],
            image_prompt=result["image_prompt"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
