# gpt_service.py
# generat_marketing_idae 함수 유지
# langchain 사용 _get_or_create_chain, generate_conversation_response 함수 추가

import os
import json
import re  # 정규식 사용 목적
import asyncio
from typing import Optional, Dict
from datetime import datetime
from enum import Enum
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.app.core.schemas import DialogueGPTResponse_AD, DialogueGPTResponse_Profile, FinalContentSchema

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ================== 대화 의도 분류 ==================

class ConversationIntent(str, Enum):
    """대화 의도 분류"""
    PROFILE_BUILDING = "profile_building"  # 첫 대화: 마케팅 전략 정보 수집 (로그인)
    GUEST_PROFILE = "guest_profile"  # 첫 대화: 축약 프로필 수집 (비로그인)
    INFO_UPDATE = "info_update"  # 정보 업데이트
    AD_GENERATION = "ad_generation"  # 광고 생성
    ANALYSIS = "analysis"  # 분석/조언


def classify_user_intent(user_input: str, has_complete_profile: bool) -> ConversationIntent:
    """
    사용자 입력의 의도를 분류
    
    Args:
        user_input: 사용자 입력 텍스트
        has_complete_profile: 프로필이 완성되었는지 여부
        
    Returns:
        ConversationIntent
    """
    
    # 첫 대화는 무조건 프로필 수집
    if not has_complete_profile:
        return ConversationIntent.PROFILE_BUILDING
    
    # 빠른 키워드 매칭
    user_input_lower = user_input.lower()
    
    # 광고 생성 관련 키워드
    ad_keywords = ['광고', '이미지', '포스터', '홍보', '배너', '만들어', '생성', '디자인', '아이디어']
    if any(keyword in user_input_lower for keyword in ad_keywords):
        return ConversationIntent.AD_GENERATION
    
    # 정보 업데이트 관련 키워드
    update_keywords = ['요즘', '요새', '최근', '지금', '바뀌', '변경', '늘었', '줄었', '많아', '적어', '달라', '다르']
    if any(keyword in user_input_lower for keyword in update_keywords):
        return ConversationIntent.INFO_UPDATE
    
    # 분석 관련 키워드
    analysis_keywords = ['왜', '이유', '분석', '어떻게', '추천', '조언', '도움']
    if any(keyword in user_input_lower for keyword in analysis_keywords):
        return ConversationIntent.ANALYSIS
    
    # 기본값: 광고 생성
    return ConversationIntent.AD_GENERATION

# langchain 변수 정의
MAX_MEMORY_TURNS = 10
parser_ad = PydanticOutputParser(pydantic_object=DialogueGPTResponse_AD)
parser_profile = PydanticOutputParser(pydantic_object=DialogueGPTResponse_Profile)

# 사용자별 대화 세션 저장 (user_id -> {chain, last_access})
CONVERSATION_MEMORIES: Dict[str, Dict] = {}

# ================== 프롬프트 템플릿들 ==================

# 1️⃣ 마케팅 전략 정보 수집 프롬프트 (첫 대화 전용)
PROFILE_BUILDING_TEMPLATE = """
당신은 소상공인 전담 마케팅 전문가입니다.

=== 사업자 기본 정보 (이미 알고 있는 정보) ===
업종: {business_type}
위치: {location}
주력 상품: {menu_items}
영업시간: {business_hours}

=== 현재 수집된 마케팅 전략 정보 ===
{existing_strategy}

=== 대화 목표 ===
이번이 첫 대화이므로, 효과적인 마케팅을 위해 다음 핵심 정보를 자연스럽게 수집하세요:

1. **타겟 고객** (연령대, 성별, 직업, 특성)
   - 예: "주로 어떤 고객층이 많이 방문하시나요?"
   
2. **차별화 포인트** (경쟁업체 대비 강점)
   - 예: "주변 {business_type}들과 비교했을 때 특별한 강점이 있으신가요?"
   
3. **브랜드 컨셉** (추구하는 이미지, 분위기)
   - 예: "어떤 분위기나 이미지를 추구하시나요?"
   
4. **마케팅 목표** (신규 고객 유치? 재방문 증대? 매출 증가?)
   - 예: "현재 가장 개선하고 싶은 부분이 있으신가요?"

=== 중요 규칙 ===
- 한 번에 하나씩만 질문하세요 (여러 질문 동시 금지)
- 자연스럽고 친근한 대화 톤 유지
- 사용자가 답변하기 쉽게 예시나 선택지 제공
- 위 4가지 정보 수집 완료 시:
  * is_complete: true
  * last_ment: "위의 대화를 반영하겠습니다" 
- 기본 정보(업종, 위치, 메뉴 등)는 절대 다시 묻지 마세요
- 같은 내용의 질문을 절대 3번 이상 반복하지 마세요

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""

# 2️⃣ 비로그인 사용자 축약 프로필 수집 및 광고 생성 프롬프트
GUEST_PROFILE_TEMPLATE = """
당신은 친근한 마케팅 어시스턴트입니다.

=== 대화 목표 ===
비로그인 사용자를 위한 빠른 광고 생성 체험을 제공합니다.
다음 3가지 정보를 수집한 후 즉시 광고를 생성하세요:

1. **업종과 위치** (예: 서울 강남 카페, 부산 해운대 음식점)
2. **사용자가 입력한 제품 사진의 설명** (예: 아메리카노, 라떼, 디저트)
3. **타겟 고객** (예: 20대 직장인, 대학생, 30대 여성)

=== 진행 단계 ===
**1~2번째 질문**: 
- 한 번에 하나씩 자연스럽게 질문
- is_complete: false
- next_question에 다음 질문 작성

**3번째 질문 응답 받은 후**:
- 수집된 정보를 바탕으로 **즉시 광고 생성**
- is_complete: true
- final_content에 광고 생성:
  * idea: 마케팅 아이디어 (구체적이고 실행 가능한 아이디어)
  * caption: 홍보 문구 (SNS 게시물용 매력적인 문구)
  * hashtags: 해시태그 리스트 (5~7개, 관련성 높은 태그)
  * image_prompt: 이미지 생성용 상세 프롬프트 (영어로 작성, Stable Diffusion용)

=== 중요 규칙 ===
- 3개 정보 수집 완료 시 **반드시 광고를 생성**하세요
- 사용자 확인 없이 바로 생성 (빠른 체험 제공)
- image_prompt는 영어로 상세하게 작성 (분위기, 색감, 구성 포함)
- 간결하고 빠르게 진행

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""

# 3️⃣ 정보 업데이트 프롬프트
INFO_UPDATE_TEMPLATE = """
당신은 소상공인 전담 마케팅 전문가입니다.

=== 사업자 정보 ===
업종: {business_type} | 위치: {location}
주력 상품: {menu_items}

=== 현재 마케팅 전략 정보 ===
{existing_strategy}

=== 대화 목표 ===
사용자가 제공한 새로운 정보를 반영하여 마케팅 전략 정보를 업데이트하세요.

=== 중요 규칙 ===
- 정보 업데이트 완료 시:
  * is_complete: true
  * last_ment: "위의 대화를 반영하겠습니다" 

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""

# 3️⃣ 광고 생성 프롬프트 (2단계: 전략 협의 → 최종 생성)
AD_GENERATION_TEMPLATE = """
당신은 소상공인 전담 마케팅 전문가입니다.

=== 사업자 정보 ===
업종: {business_type} | 위치: {location}
주력 상품: {menu_items}

=== 마케팅 전략 정보 ===
{existing_strategy}

=== 대화 목표 ===
사용자가 원하는 광고를 생성하기 위해 **전략 협의 프로세스**를 따르세요:

**📋 단계 1: 광고 전략 제안**
사용자가 광고를 요청하면, 즉시 생성하지 말고 먼저 구체적인 전략을 제안하세요:

1. **메인 메시지**: 핵심 문구 (예: "따뜻한 크리스마스, 건강한 빵과 함께")
2. **타겟 고객**: 누구를 대상으로? (기존 전략 정보 활용)
3. **비주얼 컨셉**: 어떤 느낌? (예: 아늑한, 트렌디한, 고급스러운)
4. **이미지 스타일**: 구체적인 비주얼 방향
5. **주요 요소**: 포함할 내용 (제품, 이벤트, 할인 등)

전략 제안 후 반드시:
- "이 방향으로 진행할까요?"
- "수정하고 싶은 부분이 있으면 말씀해주세요!"
- is_complete: false로 설정

**🔄 단계 2: 피드백 반영**
사용자가 수정을 요청하면:
- 피드백을 반영한 **수정된 전략**을 다시 제시
- "이렇게 수정했는데, 괜찮으신가요?"
- 여전히 is_complete: false

**✅ 단계 3: 최종 생성**
사용자가 **명확하게 동의**할 때만 최종 광고를 생성하세요.

**동의 표현 예시:**
- "좋아요", "괜찮아요", "오케이", "그렇게 해주세요"
- "만들어주세요", "생성해주세요", "진행해주세요"
- "네", "응", "예", "그래"

동의 확인 후:
- is_complete: true
- final_content에 최종 광고 생성 (idea, caption, hashtags, image_prompt)

=== 중요 규칙 ===
1. **절대 바로 생성하지 마세요**: 사용자 동의 없이 is_complete=true 금지
2. **전략만 제안**: 동의 전까지는 항상 next_question에 전략 제안
3. **명확한 동의 대기**: 애매한 반응에는 다시 확인
4. **무한 수정 가능**: 사용자가 만족할 때까지 전략 조정
5. **기존 정보 활용**: 마케팅 전략 정보를 적극 반영

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""

# 4️⃣ 분석/조언 프롬프트 (틀만)
ANALYSIS_TEMPLATE = """
당신은 소상공인 전담 마케팅 전문가입니다.

=== 사업자 정보 ===
업종: {business_type} | 위치: {location}
주력 상품: {menu_items}

=== 마케팅 전략 정보 ===
{existing_strategy}

=== 대화 목표 ===
사용자의 질문에 대해 전문적인 분석과 조언을 제공하세요.
(이 프롬프트는 향후 구현 예정)

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""


def _safe_json_from_text(text: str) -> dict:
    """
    모델이 ```json ... ``` 같은 코드블록을 섞어 보내거나
    자연어가 함께 포함되는 경우를 방어하기 위한 안전 파서 역할
    """
    # 1) 코드펜스 제거 시도 역할
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # 2) 정규식으로 가장 바깥 { ... } 객체만 추출 시도 역할
    #    - 중간에 설명 문장이 있어도 첫 JSON 오브젝트만 뽑기 목적
    match = re.search(r"\{[\s\S]*\}", cleaned)  # 줄바꿈 포함 탐색 역할
    if match:
        cleaned = match.group(0)

    # 3) json.loads 시도 및 실패 시 디버그 목적 텍스트 함께 예외 반환 역할
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT 응답 JSON 파싱 실패: {e}. 원문: {text[:300]}...")  # 과도한 로그 방지 목적

        
       

# ================== Multi-turn langchain 대화 관리 함수 ==================
def _get_or_create_chain(
    user_id: Optional[int], 
    user_context: dict = None,
    first_input: str = None
) -> tuple:
    """
    사용자별로 대화 체인 유지 + 첫 문장 의도 분류
    
    Args:
        user_id: 사용자 ID
        user_context: 사용자 컨텍스트 (첫 요청에만 제공)
        first_input: 첫 문장 (의도 분류용, 새 세션에만 제공)
        
    Returns:
        (chain, context) tuple
    """
    # 비로그인 사용자는 매번 새 체인
    if user_id is None:
        chain = _create_new_chain(user_context, first_input)
        return chain, user_context
    
    # 로그인 사용자는 기존 체인 재사용
    session_key = f"user-{user_id}"
    
    if session_key not in CONVERSATION_MEMORIES:
        # 첫 대화: 새 체인 생성 (의도 분류 포함)
        has_complete_profile = _check_profile_completeness(user_context)
        intent = classify_user_intent(first_input, has_complete_profile) if first_input else (
            ConversationIntent.PROFILE_BUILDING if not has_complete_profile else ConversationIntent.AD_GENERATION
        )
        chain = _create_new_chain(user_context, first_input)
        CONVERSATION_MEMORIES[session_key] = {
            "chain": chain,
            "user_context": user_context,
            "intent": intent,
            "last_access": datetime.now()
        }
        print(f"✅ 새 대화 세션 생성: {session_key} (의도: {intent.value})")
        return chain, user_context
    else:
        # 기존 대화: 저장된 체인 재사용
        session = CONVERSATION_MEMORIES[session_key]
        session["last_access"] = datetime.now()
        print(f"♻️  기존 대화 세션 재사용: {session_key}")
        return session["chain"], session["user_context"]


def _check_profile_completeness(context: dict) -> bool:
    """마케팅 전략 정보가 충분히 수집되었는지 확인"""
    if not context or not context.get("memory"):
        return False
    
    memory = context["memory"]
    if not memory or not hasattr(memory, 'marketing_strategy'):
        return False
    
    strategy = memory.marketing_strategy
    if not strategy:
        return False
    
    # 필수 필드 체크
    required_fields = [
        strategy.get("target_audience"),
        strategy.get("competitive_advantage"),
        strategy.get("brand_concept")
    ]
    
    return all(field is not None for field in required_fields)


def _format_strategy_info(memory) -> str:
    """마케팅 전략 정보를 읽기 쉬운 형식으로 변환"""
    if not memory or not hasattr(memory, 'marketing_strategy') or not memory.marketing_strategy:
        return "아직 수집된 정보 없음"
    
    strategy = memory.marketing_strategy
    lines = []
    
    if strategy.get("target_audience"):
        ta = strategy["target_audience"]
        lines.append(f"- 타겟 고객: {ta}")
    
    if strategy.get("competitive_advantage"):
        lines.append(f"- 차별화 포인트: {strategy['competitive_advantage']}")
    
    if strategy.get("brand_concept"):
        lines.append(f"- 브랜드 컨셉: {strategy['brand_concept']}")
    
    if strategy.get("marketing_goals"):
        lines.append(f"- 마케팅 목표: {strategy['marketing_goals']}")
    
    return "\n".join(lines) if lines else "아직 수집된 정보 없음"


def _create_new_chain(user_context: dict = None, first_input: str = None) -> ConversationChain:
    """새 LangChain ConversationChain 생성 (의도 기반 프롬프트 선택)"""
    
    # 프로필 완성 여부 확인
    has_complete_profile = _check_profile_completeness(user_context)
    
    # 의도 분류 (새 세션이고 first_input이 있을 때만)
    if first_input:
        intent = classify_user_intent(first_input, has_complete_profile)
        print(f"🎯 감지된 의도: {intent.value}")
    else:
        # first_input이 없으면 기본값
        intent = ConversationIntent.PROFILE_BUILDING if not has_complete_profile else ConversationIntent.AD_GENERATION
    
    # 의도에 맞는 프롬프트 선택
    if intent == ConversationIntent.PROFILE_BUILDING:
        template = PROFILE_BUILDING_TEMPLATE
    elif intent == ConversationIntent.INFO_UPDATE:
        template = INFO_UPDATE_TEMPLATE
    elif intent == ConversationIntent.AD_GENERATION:
        template = AD_GENERATION_TEMPLATE
    elif intent == ConversationIntent.ANALYSIS:
        template = ANALYSIS_TEMPLATE
    else:
        template = PROFILE_BUILDING_TEMPLATE
    
    # 마케팅 전략 정보 포맷팅
    strategy_text = _format_strategy_info(user_context.get("memory") if user_context else None)
    
    # 의도에 맞는 parser 선택
    selected_parser = parser_ad if intent == ConversationIntent.AD_GENERATION else parser_profile
    
    # LangChain LLM 설정
    llm = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # 메모리 설정
    memory = ConversationBufferWindowMemory(
        k=MAX_MEMORY_TURNS,
        memory_key="history"
    )
    
    # 프롬프트 구성
    prompt = PromptTemplate(
        template=template,
        input_variables=["input"],
        partial_variables={
            "format_instructions": selected_parser.get_format_instructions(),
            "business_type": user_context.get("business_type", "미확인") if user_context else "미확인",
            "location": user_context.get("location", "미확인") if user_context else "미확인",
            "menu_items": user_context.get("menu_items", "미확인") if user_context else "미확인",
            "business_hours": user_context.get("business_hours", "미확인") if user_context else "미확인",
            "existing_strategy": strategy_text
        },
    )

    # Conversation Chain 생성
    chain = ConversationChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=False 
    )
    
    return chain


async def generate_conversation_response(
    user_input: str,
    session_key: str,
    is_guest: bool = False,
    user_context: dict = None
) -> DialogueGPTResponse_AD | DialogueGPTResponse_Profile:
    """
    [비동기 버전] langchain 사용해서 multi-turn 대화 응답 생성
    
    Args:
        user_input: 사용자 입력
        session_key: 세션 키 (user-{id} or guest-{uuid})
        is_guest: 비로그인 사용자 여부
        user_context: 사용자 프로필 및 장기 메모리 (새 세션에만 제공)
    
    Returns:
        DialogueGPTResponse: 다음 질문 또는 최종 콘텐츠
    """
    try:
        # 세션 재사용 또는 새 세션 생성
        if session_key in CONVERSATION_MEMORIES:
            print(f"♻️  기존 대화 세션 재사용: {session_key}")
            memory_obj = CONVERSATION_MEMORIES[session_key]["memory"]
            chain = CONVERSATION_MEMORIES[session_key]["chain"]
            intent = CONVERSATION_MEMORIES[session_key]["intent"]
            parser = CONVERSATION_MEMORIES[session_key]["parser"]
        else:
            print(f"✅ 새 대화 세션 생성: {session_key}")
            
            # 인텐트 결정
            if is_guest:
                intent = ConversationIntent.GUEST_PROFILE
            elif user_context:
                # 로그인 사용자: 마케팅 전략 정보 완성 여부 체크
                has_complete_profile = _check_profile_completeness(user_context)
                if has_complete_profile:
                    # 프로필 완성 → 광고 생성 또는 정보 업데이트
                    intent = classify_user_intent(user_input, has_complete_profile=True)
                else:
                    # 프로필 미완성 → 상세 프로필 수집
                    intent = ConversationIntent.PROFILE_BUILDING
            else:
                # user_context 없음 → 프로필 수집
                intent = ConversationIntent.PROFILE_BUILDING
            
            print(f"🎯 감지된 의도: {intent.value}")
            
            # 프롬프트 및 파서 선택
            if intent == ConversationIntent.GUEST_PROFILE:
                template = GUEST_PROFILE_TEMPLATE
                parser = parser_ad  # 비로그인은 광고 생성으로
            elif intent == ConversationIntent.PROFILE_BUILDING:
                template = PROFILE_BUILDING_TEMPLATE
                parser = parser_profile
            elif intent == ConversationIntent.INFO_UPDATE:
                template = INFO_UPDATE_TEMPLATE
                parser = parser_profile
            elif intent == ConversationIntent.AD_GENERATION:
                template = AD_GENERATION_TEMPLATE
                parser = parser_ad
            else:
                template = PROFILE_BUILDING_TEMPLATE
                parser = parser_profile
            
            # 마케팅 전략 정보 포맷팅
            strategy_text = _format_strategy_info(user_context.get("memory") if user_context else None)
            
            # LangChain 설정
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            memory_obj = ConversationBufferWindowMemory(
                k=MAX_MEMORY_TURNS,
                memory_key="history",
                return_messages=True
            )
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["input"],
                partial_variables={
                    "format_instructions": parser.get_format_instructions(),
                    "business_type": user_context.get("business_type", "미확인") if user_context else "미확인",
                    "location": user_context.get("location", "미확인") if user_context else "미확인",
                    "menu_items": user_context.get("menu_items", "미확인") if user_context else "미확인",
                    "business_hours": user_context.get("business_hours", "미확인") if user_context else "미확인",
                    "existing_strategy": strategy_text
                },
            )
            
            chain = ConversationChain(
                llm=llm,
                prompt=prompt,
                memory=memory_obj,
                verbose=False
            )
            
            # 세션 저장
            CONVERSATION_MEMORIES[session_key] = {
                "memory": memory_obj,
                "chain": chain,
                "intent": intent,
                "parser": parser,
                "user_context": user_context
            }
        
        # langchain 실행(메모리 자동 관리 & 프롬프트 주입) - asyncio.to_thread 사용
        raw_response = await asyncio.to_thread(
            lambda: chain.invoke(input=user_input)['response'].strip()
        )
        
        # 의도 가져오기
        session = CONVERSATION_MEMORIES.get(session_key)
        intent = session.get("intent") if session else ConversationIntent.AD_GENERATION
        
        # Pydantic 모델로 변환 (이미 parser가 올바른 타입으로 파싱함)
        data = _safe_json_from_text(raw_response)
        
        if intent in [ConversationIntent.AD_GENERATION, ConversationIntent.GUEST_PROFILE]:
            # 광고 생성 모드 (로그인 AD_GENERATION + 비로그인 GUEST_PROFILE)
            response = DialogueGPTResponse_AD(**data)
        else:
            # PROFILE_BUILDING, INFO_UPDATE, ANALYSIS
            # GPT가 last_ment를 안 보내면 강제 주입
            if data.get("is_complete") and not data.get("last_ment"):
                data["last_ment"] = "위의 대화를 반영하겠습니다"
            response = DialogueGPTResponse_Profile(**data)
        
        # 대화 완료 시: 대화 기록 추출 (세션 삭제는 gpt.py에서 처리)
        if response.is_complete and session_key in CONVERSATION_MEMORIES:
            # 대화 기록 추출
            messages = memory_obj.chat_memory.messages
            conversation_history = [
                {
                    "role": "user" if msg.type == "human" else "assistant",
                    "content": msg.content
                }
                for msg in messages
            ]
            response.conversation_history = conversation_history
            print(f"📝 대화 기록 추출 완료: {len(conversation_history)}개 메시지")
        
        return response

    except Exception as e:
        raise ValueError(f"LangChain 대화 응답 생성 실패: {e}")


      
# 단일 콘텐츠 생성
async def generate_marketing_idea(prompt_text: str, context=None) -> dict:
    """
    [비동기 버전] 단일 턴에서 마케팅 아이디어 생성하는 역할
    - 마케팅 아이디어/캡션/해시태그/이미지 프롬프트 생성 역할
    - 출력 스키마를 JSON으로 강제 및 안전 파싱 역할
    """
    #( 기존 generate_marketing_idea 함수 내용은 그대로 유지)
    
    # 1) 시스템 지시문 구성 역할
    system = (
        "너는 소상공인 마케팅 도우미 역할. "
        "현재 날짜와 계절 및 시간을 고려하여 적절한 마케팅 콘텐츠를 생성해야 함. "
        "예: 11월이면 가을/겨울 이벤트, 5월이면 봄 이벤트를 제안. "
        "항상 JSON 오브젝트만 출력. 코드블록/설명/추가 문장 금지."
    )

    # 2) 사용자 프롬프트 구성 역할
    user = f"""
    아래 입력을 바탕으로 소상공인을 위한 홍보 콘텐츠를 JSON 형태로 생성해줘.

    입력:
    - 사용자 요청: {prompt_text}
    - 맥락 정보: {context or '날씨, 업종, 분위기 등'}

    출력(JSON 오브젝트만, 추가 텍스트/코드블록 금지):
    출력(JSON 형식으로만, ``json 블록 없이):
    {{
     "idea": "짧은 이벤트 아이디어 문장",
      "caption": "홍보용 문구(짧고 감성적인 문장)",
      "hashtags": ["#예시", "#홍보", "#지역명"],
      "image_prompt": "Stable Diffusion용 영어 프롬프트"
    }}
    """.strip()

    try:
        # 3) Chat Completions 호출 역할
        #    - 가능 모델의 경우 JSON 강제 포맷 지정 역할
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            # 지원되는 모델인 경우만 동작. 미지원이면 제거 필요성.
            response_format={"type": "json_object"},
        )

        # 4) 콘텐츠 추출 및 널/인덱스 보호 역할
        if not res.choices or not res.choices[0].message or not res.choices[0].message.content:
            raise ValueError("모델 응답 비정상: content 없음")

        content = res.choices[0].message.content.strip()
        # 5) 안전 파싱 수행 역할
        data = _safe_json_from_text(content)


        # 6) 스키마 보정(타입/필드 기본값 채우기) 역할
        idea = data.get("idea", "").strip()
        caption = data.get("caption", "").strip()
        hashtags = data.get("hashtags", [])
        image_prompt = data.get("image_prompt", "").strip()

        if not isinstance(hashtags, list):
            hashtags = []
        # 7) 최소 필수값 점검 역할
        if not image_prompt:
            # image_prompt 누락 시 캡션/아이디어 기반 기본 프롬프트 생성 보정 역할
            fallback = "clean promotional poster, high quality, modern typography"
            image_prompt = f"{caption or idea}, {fallback}"

        return {
            "idea": idea,
            "caption": caption,
            "hashtags": hashtags,
            "image_prompt": image_prompt
        }

    except Exception as e:
        # 8) 최종 예외 단일화 및 상위 레이어 전달 역할
        raise ValueError(f"GPT 생성 실패: {e}")

async def extract_city_name_english(location: str) -> str:
    """
    [비동기 버전] 한글 지역명을 GPT를 사용하여 영어 도시명으로 변환
    예: "서울 강남구" -> "Seoul"
        "부산광역시 해운대구" -> "Busan"
    """
    import re
    
    # 이미 영어인 경우 그대로 반환
    if re.match(r'^[a-zA-Z\s]+$', location):
        return location.split()[0]  # 첫 단어만 반환
    
    # 위치 정보가 없으면 기본값
    if not location or location.strip() == "":
        return "Seoul"
    
    try:
        prompt = f"""
        다음 한국어 지역명을 날씨 API에서 사용할 수 있는 영어 도시명으로 변환해줘.
        도시명만 간단하게 반환하고, 추가 설명은 하지 마('서울 강남구' -> 'Seoul' 처럼).
        
        입력: {location}
        출력 형식: 영어 도시명 (예: Seoul, Busan, Incheon)
        """
        
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # 낮은 temperature로 일관된 결과
            max_tokens=20     # 짧은 응답만 필요
        )
        
        city_name = res.choices[0].message.content.strip()
        
        # 결과 검증 (영어만 포함되어야 함)
        if re.match(r'^[a-zA-Z\s-]+$', city_name):
            # 여러 단어가 있으면 첫 번째 단어만 (예: "Seoul City" -> "Seoul")
            return city_name.split()[0]
        else:
            # 예상치 못한 형식이면 기본값
            return "Seoul"
            
    except Exception as e:
        print(f"[지역명 변환 오류]: {e}")
        return "Seoul"  # 실패 시 기본값
