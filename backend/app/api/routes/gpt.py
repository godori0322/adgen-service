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
from backend.app.services.gpt_service import generate_conversation_response, CONVERSATION_MEMORIES
from backend.app.core.schemas import GPTRequest, GPTResponse, DialogueGPTResponse, FinalContentSchema
from backend.app.core.database import get_db
from backend.app.services import auth_service, memory_service

# new 요청 스키마
class DialogueRequest(BaseModel):
    user_input: str = Field(..., description="사용자가 입력한 대화 내용")
    # session_id 제거: 서버에서 자동 생성

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
@router.post("/dialogue")
async def handle_marketing_dialog(
    request: DialogueRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    langchain 활용 multi-turn 대화 처리
    
    - 로그인 사용자: 장기 메모리 + 프로필 반영
    - 비로그인 사용자: 메모리 없이 매번 새 대화
    """
    try:
        # 1. 사용자 인증 (optional)
        token = credentials.credentials if credentials else None
        current_user = auth_service.get_user_from_token(db, token)
        
        # 2. 세션 존재 여부 확인
        session_key = f"user-{current_user.id}" if current_user else None
        session_exists = session_key and session_key in CONVERSATION_MEMORIES
        
        # 3. 사용자 컨텍스트 구성 (첫 요청에만 DB 쿼리)
        user_context = None
        if current_user and not session_exists:
            # 첫 대화: 프로필 + 장기 메모리 조회
            menu_items_str = None
            if current_user.menu_items:
                try:
                    menu_list = json.loads(current_user.menu_items)
                    menu_items_str = ", ".join(menu_list)
                except:
                    menu_items_str = current_user.menu_items
            
            # 장기 메모리 조회 (DB 쿼리 10-30ms)
            long_term_memory = memory_service.get_user_memory(db, current_user.id)
            
            user_context = {
                "business_type": current_user.business_type,
                "location": current_user.location,
                "menu_items": menu_items_str,
                "business_hours": current_user.business_hours,
                "memory": long_term_memory  # 장기 메모리 추가
            }
            print(f"📊 첫 대화: 사용자 컨텍스트 조회 완료 (user_id={current_user.id})")
        elif session_exists:
            print(f"⚡ 세션 재사용: DB 쿼리 스킵 (user_id={current_user.id})")
        
        # 4. 대화 진행 (세션 재사용 시 캐싱된 컨텍스트 사용)
        response = generate_conversation_response(
            user_input=request.user_input,
            user_id=current_user.id if current_user else None,
            user_context=user_context  # 첫 요청: 딕셔너리, 이후: None (세션에서 재사용)
        )
        
        # 5. 대화 완료 시 메모리 업데이트 (로그인 사용자만)
        if response.is_complete and response.final_content and current_user:
            try:
                # 대화 요약 (최종 콘텐츠 기반)
                summary = memory_service.create_conversation_summary(
                    final_content=response.final_content.dict()
                )
                
                # 추출된 정보
                insights = memory_service.extract_insights_from_final_content(
                    response.final_content.dict()
                )
                
                # 장기 메모리 업데이트
                memory_service.update_user_memory(
                    db=db,
                    user_id=current_user.id,
                    conversation_summary=summary,
                    new_insights=insights
                )
                
            except Exception as mem_err:
                print(f"⚠️ 메모리 업데이트 실패 (비치명적): {mem_err}")
                # 메모리 업데이트 실패해도 응답은 반환
        
        # 6. 응답 반환
        return {
            "is_complete": response.is_complete,
            "next_question": response.next_question,
            "final_content": response.final_content.dict() if response.final_content else None
        }
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 서비스 오류: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

#