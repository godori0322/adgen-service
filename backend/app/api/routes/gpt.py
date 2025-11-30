# gpt.py

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
import json
import base64
# 기존
from backend.app.services.gpt_service import generate_marketing_idea
# 추가
from backend.app.services.gpt_service import generate_conversation_response, CONVERSATION_MEMORIES
from backend.app.core.schemas import GPTRequest, GPTResponse, DialogueGPTResponse_AD, DialogueGPTResponse_Profile, FinalContentSchema
from backend.app.core.database import get_db
from backend.app.services import auth_service, memory_service

# new 요청 스키마
class DialogueRequest(BaseModel):
    user_input: str = Field(..., description="사용자가 입력한 대화 내용")
    guest_session_id: Optional[str] = Field(None, description="비로그인 사용자 세션 ID (프론트엔드 생성)")

router = APIRouter(prefix="/gpt", tags=["GPT"])
security = HTTPBearer(auto_error=False)


# endpoint
# 기존 : 단일 턴 마케팅 콘텐츠 생성
@router.post("/generate", response_model=GPTResponse)
async def generate_marketing_content(req: GPTRequest):
    try:
        result = await generate_marketing_idea(
            prompt_text=req.text,
            context=req.context
        )
        return GPTResponse(
            idea=result["idea"],
            caption=result["caption"],
            hashtags=result["hashtags"],
            image_prompt=result["image_prompt"],
            bgm_prompt=result.get("bgm_prompt"),
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
        
        # 2. 세션 키 결정
        if current_user:
            session_key = f"user-{current_user.id}"
            is_guest = False
        elif request.guest_session_id:
            session_key = f"guest-{request.guest_session_id}"
            is_guest = True
        else:
            raise HTTPException(status_code=400, detail="로그인하거나 guest_session_id를 제공하세요")
        
        session_exists = session_key in CONVERSATION_MEMORIES
        
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
        elif session_exists and current_user:
            print(f"⚡ 세션 재사용: DB 쿼리 스킵 (user_id={current_user.id})")
        elif session_exists and is_guest:
            print(f"⚡ 게스트 세션 재사용: {session_key}")
        
        # 4. 대화 진행 (세션 재사용 시 캐싱된 컨텍스트 사용)
        response = await generate_conversation_response(
            user_input=request.user_input,
            session_key=session_key,
            is_guest=is_guest,
            user_context=user_context  # 첫 요청: 딕셔너리, 이후: None (세션에서 재사용)
        )
        
        # 5. 대화 완료 시 처리
        if response.is_complete:
            # 세션 삭제
            if session_key in CONVERSATION_MEMORIES:
                del CONVERSATION_MEMORIES[session_key]
                print(f"🗑️  대화 완료, 세션 삭제: {session_key}")
            
            # 로그인 사용자만 메모리 업데이트
            if current_user:
                try:
                    # final_content가 있으면 포함, 없으면 None 전달
                    final_content_dict = None
                    if hasattr(response, 'final_content') and response.final_content:
                        final_content_dict = response.final_content.dict()
                    
                    # 장기 메모리 업데이트 (비동기 - GPT API + 임베딩)
                    await memory_service.update_user_memory(
                        db=db,
                        user_id=current_user.id,
                        conversation_history=response.conversation_history,
                        final_content=final_content_dict
                    )
                    print(f"✅ 장기 메모리 업데이트 완료 (JSON 형식)")
                    
                except Exception as mem_err:
                    print(f"⚠️ 메모리 업데이트 실패 (비치명적): {mem_err}")
                    # 메모리 업데이트 실패해도 응답은 반환
        
        # 6. 응답 반환 - session_key 설정 (model_copy 사용)
        return response.model_copy(update={"session_key": session_key})
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 서비스 오류: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")


@router.post("/dialogue/upload-image")
async def upload_product_image(
    session_key: str = Form(..., description="세션 키 (user-{id} 또는 guest-{uuid})"),
    product_image: UploadFile = File(..., description="제품 사진 파일")
):
    """
    대화 세션에 제품 이미지 업로드
    
    - session_key: 백엔드가 생성한 세션 키
    - product_image: 제품 사진 파일 (jpg, png 등)
    
    Returns:
        - message: 성공 메시지
        - image_size: 업로드된 이미지 크기 (bytes)
    """
    try:
        # 1. 세션 존재 확인
        if session_key not in CONVERSATION_MEMORIES:
            raise HTTPException(
                status_code=404, 
                detail=f"세션을 찾을 수 없습니다: {session_key}"
            )
        
        # 2. 이미지 읽기
        image_bytes = await product_image.read()
        
        # 3. base64로 인코딩
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 4. 세션에 저장
        CONVERSATION_MEMORIES[session_key]["product_image"] = image_base64
        
        print(f"📸 제품 이미지 업로드 완료: {session_key} ({len(image_bytes)} bytes)")
        
        return {
            "message": "이미지 업로드 성공",
            "image_size": len(image_bytes),
            "session_key": session_key
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 업로드 실패: {str(e)}"
        )
