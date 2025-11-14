# gpt.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
# 기존
from backend.app.services.gpt_service import generate_marketing_idea
# 추가
from backend.app.services.gpt_service import generate_conversation_response
from backend.app.core.schemas import GPTRequest, GPTResponse, DialogueGPTResponse, FinalContentSchema

# new 요청 스키마
class DialogueRequest(BaseModel):
    session_id: str = Field(..., description="대화를 추적하기 위한 고유 세션 ID")
    user_input: str = Field(..., descriptioin="사용자가 입력한 대화 내용")

router = APIRouter(prefix="/gpt", tags=["GPT"])


# endpoint
# 기존 : 단일 턴 마케팅 콘텐츠 생성
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

# 추가: multi-turn 대화 API : dialogue 요청 처리
@router.post("/dialogue", response_model=DialogueGPTResponse | FinalContentSchema)
async def handle_marketing_dialog(request: DialogueRequest):
    """langchain 활용 multi-turn 대화 처리, 다음 질문 or 최종 콘텐츠 반환"""
    try:
        # gpt_service.py의 langchain 함수 호출
        response = generate_conversation_response(
            session_id = request.session_id,
            user_input = request.user_input
        )
        return response
    
    except ValueError as e:
        # gpt 서비스 레이어에서 발생(e.g. json 파싱실패) cjfl
        raise HTTPException(status_code=500, detail=f"GPT 응답 서비스 오류: {e}")
    except Exception as e:
        # 기타 예외 처리
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

#