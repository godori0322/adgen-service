# memory_service.py
# 사용자 메모리 관리 서비스 (자연어 + 임베딩)

import os
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from backend.app.core.models import UserMemory

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str) -> List[float]:
    """[비동기] 텍스트를 임베딩 벡터로 변환 (OpenAI text-embedding-3-small)"""
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def get_user_memory(db: Session, user_id: int) -> Optional[UserMemory]:
    """사용자의 장기 메모리 조회 (최신 하나)"""
    memory = db.query(UserMemory).filter(
        UserMemory.user_id == user_id
    ).order_by(UserMemory.updated_at.desc()).first()
    
    return memory


async def extract_marketing_strategy_from_conversation(
    conversation_history: List[dict],
    final_content: dict,
    existing_strategy: dict = None
) -> dict:
    """
    [비동기] 대화 기록에서 마케팅 전략 정보를 구조화하여 추출
    
    Args:
        conversation_history: 전체 대화 기록
        final_content: 최종 생성된 콘텐츠
        existing_strategy: 기존 전략 정보
        
    Returns:
        MarketingStrategy 형태의 딕셔너리
    """
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""
다음 대화에서 마케팅 전략 정보를 추출하여 JSON 형식으로 반환하세요.

기존 정보:
{json.dumps(existing_strategy, ensure_ascii=False) if existing_strategy else "없음"}

대화 기록:
{conversation_text}

최종 콘텐츠:
{json.dumps(final_content, ensure_ascii=False)}

다음 JSON 형식으로 출력하세요 (대화에서 언급되지 않은 필드는 null):
{{
  "target_audience": {{
    "age_group": ["20대", "30대"] or null,
    "occupation": ["직장인"] or null,
    "gender": "여성" or null,
    "characteristics": ["특성1", "특성2"] or null
  }},
  "competitive_advantage": ["강점1", "강점2"] or null,
  "brand_concept": {{
    "keywords": ["키워드1", "키워드2"] or null,
    "tone": "톤앤매너" or null
  }},
  "marketing_goals": ["목표1", "목표2"] or null,
  "preferences": {{
    "channels": ["채널1"] or null,
    "content_style": ["스타일1"] or null
  }}
}}

기존 정보가 있으면 병합하고, 새 정보로 업데이트하세요.
"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        extracted = json.loads(response.choices[0].message.content)
        
        # 기존 정보와 병합
        if existing_strategy:
            merged = existing_strategy.copy()
            for key, value in extracted.items():
                if value is not None:
                    if isinstance(value, dict) and key in merged and merged[key]:
                        # 딕셔너리는 병합
                        merged[key] = {**merged.get(key, {}), **value}
                    elif isinstance(value, list) and key in merged and merged[key]:
                        # 리스트는 중복 제거 후 병합
                        existing_list = merged.get(key, [])
                        merged[key] = list(set(existing_list + value))
                    else:
                        merged[key] = value
            return merged
        else:
            return extracted
            
    except Exception as e:
        print(f"⚠️ 마케팅 전략 추출 실패: {e}")
        return existing_strategy or {}


async def update_user_memory(
    db: Session, 
    user_id: int, 
    conversation_history: List[dict],
    final_content: dict
) -> UserMemory:
    """
    [비동기] 대화 기록에서 마케팅 전략 정보를 추출하여 JSON 형식으로 저장
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        conversation_history: 전체 대화 기록
        final_content: 최종 생성된 콘텐츠
    
    Returns:
        업데이트된 UserMemory 객체
    """
    print(f"🔍 update_user_memory 시작 - user_id: {user_id}")
    
    # 1. 기존 메모리 조회 (동기 - 빠른 DB 조회)
    existing_memory = db.query(UserMemory).filter(
        UserMemory.user_id == user_id
    ).order_by(UserMemory.updated_at.desc()).first()
    
    print(f"📦 기존 메모리: {'있음' if existing_memory else '없음'}")
    
    existing_strategy = existing_memory.marketing_strategy if existing_memory else None
    
    # 2. 대화에서 마케팅 전략 정보 추출 (비동기 - GPT API)
    print(f"🤖 GPT로 전략 정보 추출 시작...")
    updated_strategy = await extract_marketing_strategy_from_conversation(
        conversation_history,
        final_content,
        existing_strategy
    )
    print(f"✅ 추출된 전략: {json.dumps(updated_strategy, ensure_ascii=False)[:200]}...")
    
    # 3. 임베딩 생성 (비동기 - OpenAI API)
    print(f"🔢 임베딩 생성 중...")
    embedding_text = json.dumps(updated_strategy, ensure_ascii=False)
    embedding = await get_embedding(embedding_text)
    print(f"✅ 임베딩 생성 완료: {len(embedding) if embedding else 0}차원")
    
    # 4. DB 저장/업데이트 (동기 - 빠른 작업)
    if existing_memory:
        print(f"🔄 기존 메모리 업데이트...")
        existing_memory.marketing_strategy = updated_strategy
        existing_memory.embedding = embedding
        db.commit()
        db.refresh(existing_memory)
        print(f"✅ 업데이트 완료 - memory_id: {existing_memory.id}")
        return existing_memory
    else:
        print(f"🆕 새 메모리 생성...")
        new_memory = UserMemory(
            user_id=user_id,
            marketing_strategy=updated_strategy,
            embedding=embedding
        )
        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)
        print(f"✅ 생성 완료 - memory_id: {new_memory.id}")
        return new_memory






