# memory_service.py
# 사용자 메모리 관리 서비스 (자연어 + 임베딩)

import os
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from openai import OpenAI
from backend.app.core.models import UserMemory

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> List[float]:
    """텍스트를 임베딩 벡터로 변환 (OpenAI text-embedding-3-small)"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def get_user_memory(db: Session, user_id: int) -> Optional[str]:
    """사용자의 장기 메모리 조회 (최신 하나)"""
    memory = db.query(UserMemory).filter(
        UserMemory.user_id == user_id
    ).order_by(UserMemory.updated_at.desc()).first()
    
    return memory.memory_text if memory else None


def update_user_memory(
    db: Session, 
    user_id: int, 
    conversation_summary: str,
    new_insights: dict
) -> UserMemory:
    """
    GPT를 활용하여 기존 메모리 + 새로운 대화 내용을 통합
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        conversation_summary: 이번 대화 요약
        new_insights: 추출된 새로운 정보 (dict)
    
    Returns:
        업데이트된 UserMemory 객체
    """
    # 1. 기존 메모리 조회
    existing_memory = db.query(UserMemory).filter(
        UserMemory.user_id == user_id
    ).order_by(UserMemory.updated_at.desc()).first()
    
    existing_text = existing_memory.memory_text if existing_memory else ""
    
    # 2. GPT에게 메모리 업데이트 요청
    updated_memory_text = _merge_memory_with_gpt(
        existing_memory=existing_text,
        conversation_summary=conversation_summary,
        new_insights=new_insights
    )
    
    # 3. 임베딩 생성
    embedding = get_embedding(updated_memory_text)
    
    # 4. DB 저장/업데이트
    if existing_memory:
        existing_memory.memory_text = updated_memory_text
        existing_memory.embedding = embedding
        db.commit()
        db.refresh(existing_memory)
        return existing_memory
    else:
        new_memory = UserMemory(
            user_id=user_id,
            memory_text=updated_memory_text,
            embedding=embedding
        )
        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)
        return new_memory


def _merge_memory_with_gpt(
    existing_memory: str,
    conversation_summary: str,
    new_insights: dict
) -> str:
    """GPT를 활용하여 기존 메모리와 새 정보를 통합"""
    
    prompt = f"""
우리가 제공하는 서비스는 소상공인을 위한 마케팅 서비스입니다.(생성형 AI로 광고이미지와 문구를 생성해서 사용자에게 제공합니다.) 
우리 서비스는 사용자 맞춤형으로 이전 대화를 통해 사용자의 사업장 정보를 반영하고 기록합니다. 당신이 소상공인 담당 마케터라고 가정하고
마케팅에 필요한 기존 메모리와 새로운 대화 내용을 통합하여 업데이트된 메모리를 생성하세요.(메모리는 텍스트 형태로 관리합니다)

### 규칙:
1. **중복 제거**: 기존 정보와 중복되는 내용은 추가하지 마세요
2. **새 정보 추가**: 새롭게 알게 된 사실만 추가하세요
3. **시즌/이벤트 정보 정리**: 
   - **계절 이벤트**: 계절이 바뀌면 이전 계절 이벤트 정보 삭제 (예: 여름 메뉴 추가 시 겨울 할인 정보 제거)
   - **기간 한정**: 종료되거나 과거의 프로모션은 제거
   - **현재성 우선**: 최근 1~2개 이벤트만 유지, 오래된 정보는 삭제
4. **간결함 유지**: 핵심만 담아 3~4 문단 이내로 작성하세요
5. **자연스러운 문장**: 불필요한 형식 없이 자연스러운 문장으로 작성하세요

### 기존 메모리:
{existing_memory if existing_memory else "(메모리 없음)"}

### 새로운 대화 요약:
{conversation_summary}

### 추출된 새 정보:
{json.dumps(new_insights, ensure_ascii=False, indent=2)}

### 업데이트된 메모리 (중복 없이, 자연스럽게):
""".strip()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        updated_memory = response.choices[0].message.content.strip()
        return updated_memory
    
    except Exception as e:
        print(f"❌ Memory merge failed: {e}")
        # 폴백: 기존 메모리 + 새 정보 단순 결합
        if existing_memory:
            return f"{existing_memory}\n\n{conversation_summary}"
        else:
            return conversation_summary


def create_conversation_summary(final_content: dict) -> str:
    """최종 콘텐츠에서 대화 요약 생성 (간단한 텍스트)"""
    
    prompt = f"""
우리가 제공하는 서비스는 소상공인을 위한 사용자 맞춤형 마케팅 서비스입니다.(생성형 AI로 광고이미지와 문구를 생성해서 사용자에게 제공합니다.)

다음 마케팅 콘텐츠 생성 결과를 간단히 요약하세요:

최종 생성물:
{json.dumps(final_content, ensure_ascii=False)}

요약 (한 문단, 핵심만):
""".strip()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ Conversation summary failed: {e}")
        # 폴백
        return f"사용자가 {final_content.get('idea', '마케팅 콘텐츠')}를 요청했습니다."


def extract_insights_from_final_content(final_content: dict) -> dict:
    """최종 콘텐츠에서 핵심 정보 추출"""
    insights = {}
    
    if "idea" in final_content:
        insights["generated_idea"] = final_content["idea"]
    
    if "caption" in final_content:
        insights["caption_style"] = final_content["caption"]
    
    if "hashtags" in final_content and final_content["hashtags"]:
        insights["preferred_hashtags"] = final_content["hashtags"][:5]  # 상위 5개만
    
    return insights
