# gpt.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
import json
# 기존
from backend.app.services.gpt_service import generate_marketing_idea
# 추가
from backend.app.services.gpt_service import generate_conversation_response
from backend.app.core.schemas import GPTRequest, GPTResponse, DialogueGPTResponse, FinalContentSchema
from backend.app.core.database import get_db
from backend.app.services import auth_service

# new 요청 스키마
class DialogueRequest(BaseModel):
    session_id: str = Field(..., description="대화를 추적하기 위한 고유 세션 ID")
    user_input: str = Field(..., descriptioin="사용자가 입력한 대화 내용")

router = APIRouter(prefix="/gpt", tags=["GPT"])
security = HTTPBearer(auto_error=False)


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
async def handle_marketing_dialog(
    request: DialogueRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """langchain 활용 multi-turn 대화 처리, 다음 질문 or 최종 콘텐츠 반환"""
    try:
        # 토큰에서 사용자 정보 추출 (optional)
        token = credentials.credentials if credentials else None
        current_user = auth_service.get_user_from_token(db, token)
        
        # 사용자 컨텍스트 생성
        user_context = None
        if current_user:
            menu_items_str = None
            if current_user.menu_items:
                try:
                    menu_list = json.loads(current_user.menu_items)
                    menu_items_str = ", ".join(menu_list)
                except:
                    menu_items_str = current_user.menu_items
            
            user_context = {
                "business_type": current_user.business_type,
                "location": current_user.location,
                "menu_items": menu_items_str,
                "business_hours": current_user.business_hours
            }
        
        # gpt_service.py의 langchain 함수 호출
        response = generate_conversation_response(
            session_id=request.session_id,
            user_input=request.user_input,
            user_context=user_context
        )
        return response
    
    except ValueError as e:
        # gpt 서비스 레이어에서 발생(e.g. json 파싱실패)
        raise HTTPException(status_code=500, detail=f"GPT 응답 서비스 오류: {e}")
    except Exception as e:
        # 기타 예외 처리
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

#