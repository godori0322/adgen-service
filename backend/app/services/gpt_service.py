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
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from backend.app.core.schemas import DialogueGPTResponse_AD, DialogueGPTResponse_Profile, FinalContentSchema

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ================== 대화 의도 분류 ==================

class ConversationIntent(str, Enum):
    """대화 의도 분류"""
    PROFILE_BUILDING = "profile_building"  # 첫 대화: 마케팅 전략 정보 수집 (로그인)
    GUEST_PROFILE = "guest_profile"  # 첫 대화: 축약 프로필 수집 (비로그인)
    GUEST_AD_GENERATION = "guest_ad_generation"  # 비로그인 광고 생성 (정보 수집 완료 후)
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
    update_keywords = ['요즘', '요새', '최근', '지금', '바뀌', '변경', '늘었', '줄었', '많아', '적어', '달라', '다르', '추가', '새로']
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

# 사용자 컨텍스트 영구 저장 (세션 종료 후에도 유지)
USER_CONTEXTS: Dict[str, Dict] = {}

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
비로그인 사용자를 위한 빠른 정보 수집을 진행합니다.
다음 3가지 정보를 수집하세요:

1. **업종과 위치** (예: 서울 강남 카페, 부산 해운대 음식점)
2. **주요 메뉴들** (예: 아메리카노, 라떼, 디저트)
3. **타겟 고객** (예: 20대 직장인, 대학생, 30대 여성)

=== 진행 단계 ===
**1~2번째 질문**: 
- 한 번에 하나씩 자연스럽게 질문
- is_complete: false
- next_question에 다음 질문 작성

**3번째 질문 응답 받은 후**:
- 정보 수집 완료
- is_complete: true
- final_content에 광고 생성:
  * idea: 마케팅 아이디어 (구체적이고 실행 가능한 아이디어)
  * caption: 홍보 문구 (SNS 게시물용 매력적인 문구)
  * hashtags: 해시태그 리스트 (5~7개, 관련성 높은 태그)
  * image_prompt: 이미지 생성용 상세 프롬프트 (영어로 작성, Stable Diffusion용)
  * bgm_prompt: MusicGen에서 바로 사용할 수 있는 영어 한 문장.
      - 반드시 포함할 요소:
        - 장르(genre): lo-fi hip hop, jazz, ambient 등
        - 분위기(mood): cozy, energetic, dreamy, calm 등
        - 템포(tempo): BPM(예: 80-90 BPM) 또는 slow/medium/fast
        - 악기(instruments): piano, guitar, strings, soft drums 등
        - 사용 맥락(context): small cafe, hair salon, casual restaurant 등
      - 예시:
        "warm lo-fi hip hop instrumental, cozy and relaxed mood, 80-90 BPM, soft piano and light drums, background music for a small neighborhood cafe"


=== 중요 규칙 ===
- 3개 정보 수집 완료 시 is_complete: true로 설정
- 광고는 생성하지 않습니다 (다음 대화에서 생성)
- 간결하고 빠르게 진행
- 친근한 톤 유지
- 같은 질문은 절대 3번 이상 반복하지 마세요

=== 현재 대화 ===
{history}

사용자: {input}

다음 JSON 형식으로 응답:
{format_instructions}
"""

# 2-2️⃣ 비로그인 사용자 광고 생성 프롬프트 (정보 수집 완료 후)
GUEST_AD_GENERATION_TEMPLATE = """
당신은 소상공인 전담 마케팅 전문가입니다.

=== 사업자 정보 (비로그인 사용자가 제공한 정보) ===
업종: {business_type}
위치: {location}
주력 상품: {menu_items}
타겟 고객: {existing_strategy}

=== 대화 목표 ===
사용자가 원하는 광고를 생성하기 위해 **전략 협의 프로세스**를 따르세요:

**📋 단계 1: 광고 전략 제안**
사용자가 광고를 요청하면, 즉시 생성하지 말고 먼저 구체적인 전략을 제안하세요:

1. **메인 메시지**: 핵심 문구 (예: "따뜻한 크리스마스, 건강한 빵과 함께")
2. **타겟 고객**: 누구를 대상으로? (위 타겟 고객 정보 활용)
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
5. **수집된 정보 활용**: 위 사업자 정보를 적극 반영

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

----------------------------------------
✅ 단계 3: 최종 생성
----------------------------------------
사용자가 **전략 동의 + 생성 방식 선택** 두 가지 모두 완료한 뒤 최종 광고를 생성합니다.

**동의 표현 예시**
- "좋아요", "괜찮아요", "그렇게 해주세요"
- "만들어주세요", "생성해주세요", "진행해주세요"

동의 확인 + 생성 방식 선택 완료 시:
- is_complete: true
- final_content에 아래 항목 모두 포함:
  * idea: 마케팅 아이디어
  * caption: 홍보 문구
  * hashtags: SNS 해시태그 리스트
  * image_prompt: 이미지 생성 프롬프트
  * bgm_prompt: MusicGen 프롬프트


=== 중요 규칙 ===
1. **절대 바로 생성하지 마세요**: 사용자 동의 없이 is_complete=true 금지
2. **전략만 제안**: 동의 전까지는 항상 next_question에 전략 제안
3. **명확한 동의 대기**: 애매한 반응에는 다시 확인
4. **무한 수정 가능**: 사용자가 만족할 때까지 전략 조정
5. **기존 정보 활용**: 마케팅 전략 정보를 적극 반영
6. **한글, 영어 구분**: idea, caption, hashtags는 한글로 image_prompt, bgm_prompt는 영어로 작성

=== 출력 형식 ===
최종 광고를 생성할 때(final_content에 담을 때) 필드는 다음과 같이 구성:

- idea: 마케팅 아이디어 (구체적이고 실행 가능한 아이디어)
- caption: 홍보 문구 (SNS 게시물용 매력적인 문구)
- hashtags: 해시태그 리스트 (5~7개, 관련성 높은 태그)
- image_prompt: 이미지 생성용 상세 프롬프트 (영어로 작성, Stable Diffusion용)
- bgm_prompt

bgm_prompt는 MusicGen에서 바로 사용할 수 있는 영어 문장이어야 하며 아래 요소를 반드시 포함:
    - 장르(genre): lo-fi hip hop, jazz, ambient 등
    - 분위기(mood): cozy, energetic, dreamy, calm 등
    - 템포(tempo): BPM(예: 80-90 BPM) 또는 slow/medium/fast
    - 악기(instruments): piano, guitar, strings, soft drums 등
    - 사용 맥락(context): small cafe, hair salon, casual restaurant 등
- 예시:
    "warm lo-fi hip hop instrumental, cozy and relaxed mood, 80-90 BPM, soft piano and light drums, background music for a small neighborhood cafe"


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
            session = CONVERSATION_MEMORIES[session_key]
            memory_obj = session["memory"]
            chain = session["chain"]
            intent = session["intent"]
            parser = session["parser"]
                
        else:
            print(f"✅ 새 대화 세션 생성: {session_key}")
            
            # 인텐트 결정
            if is_guest:
                # 비로그인 사용자: user_context 존재 여부로 판단
                if user_context and user_context.get("business_type") and user_context.get("business_type") != "미확인":
                    # 정보 수집 완료 → 광고 생성 모드
                    intent = ConversationIntent.GUEST_AD_GENERATION
                    print(f"🎯 비로그인 사용자 정보 있음 → 광고 생성 모드")
                else:
                    # 정보 수집 필요 → 프로필 수집 모드
                    intent = ConversationIntent.GUEST_PROFILE
                    print(f"🆕 비로그인 사용자 정보 없음 → 프로필 수집 모드")
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
                parser = parser_profile  # 비로그인 첫 대화는 정보 수집 스키마
            elif intent == ConversationIntent.GUEST_AD_GENERATION:
                template = GUEST_AD_GENERATION_TEMPLATE
                parser = parser_ad
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
                "user_context": user_context  # 로그인/비로그인 모두 동일하게 관리
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
        
        if intent in [ConversationIntent.AD_GENERATION, ConversationIntent.GUEST_AD_GENERATION]:
            # 광고 생성 모드 (로그인 AD_GENERATION + 비로그인 GUEST_AD_GENERATION)
            data["type"] = "ad"  # type 필드 강제 주입
            response = DialogueGPTResponse_AD(**data)
            
            # ----------------------------------------
            # bgm_prompt 최소 검증 + 보정
            # ----------------------------------------
            if response.final_content:
                bgm_prompt = (response.final_content.bgm_prompt or "").strip()

                # 1) 비어 있으면 기본값으로 교체
                if not bgm_prompt:
                    bgm_prompt = (
                        "warm lo-fi hip hop instrumental, cozy and relaxed mood, "
                        "80-90 BPM, soft piano and light drums, "
                        "background music for a small neighborhood cafe"
                    )
                else:
                    # 2) 너무 짧으면 (단어 5개 미만) 기본값으로 교체
                    if len(bgm_prompt.split()) < 5:
                        bgm_prompt = (
                            "warm lo-fi hip hop instrumental, cozy and relaxed mood, "
                            "80-90 BPM, soft piano and light drums, "
                            "background music for a small neighborhood cafe"
                        )

                # 3) pydantic 객체 업데이트
                updated_final_content = response.final_content.model_copy(
                    update={"bgm_prompt": bgm_prompt}
                )
                response = response.model_copy(update={"final_content": updated_final_content})
                           
        else:
            # PROFILE_BUILDING, INFO_UPDATE, ANALYSIS, GUEST_PROFILE
            data["type"] = "profile"  # type 필드 강제 주입
            # GPT가 last_ment를 안 보내면 강제 주입
            if data.get("is_complete") and not data.get("last_ment"):
                data["last_ment"] = "위의 대화를 반영하겠습니다"
            response = DialogueGPTResponse_Profile(**data)
        
        # 대화 완료 시: 대화 기록 추출 + Vision 통합 (세션 삭제는 gpt.py에서 처리)
        if response.is_complete and session_key in CONVERSATION_MEMORIES:
            # 비로그인 사용자 첫 대화 완료: 정보 저장
            if is_guest and intent == ConversationIntent.GUEST_PROFILE:
                print("✅ 비로그인 사용자 정보 수집 완료")
                
                # 대화 히스토리에서 정보 추출
                messages = memory_obj.chat_memory.messages
                
                # 간단한 정보 추출: 사용자가 말한 내용에서 추출
                collected_info = {
                    "business_type": "미확인",
                    "location": "미확인",
                    "menu_items": "미확인",
                    "target_audience": "미확인"
                }
                
                # 사용자 응답만 추출하여 저장 (간단한 방식)
                user_responses = [msg.content for msg in messages if msg.type == "human"]
                if len(user_responses) >= 1:
                    collected_info["business_type"] = user_responses[0] if len(user_responses) > 0 else "미확인"
                if len(user_responses) >= 2:
                    collected_info["menu_items"] = user_responses[1] if len(user_responses) > 1 else "미확인"
                if len(user_responses) >= 3:
                    collected_info["target_audience"] = user_responses[2] if len(user_responses) > 2 else "미확인"
                
                # location은 business_type에서 추출 시도 (예: "서울 강남 카페" → location: "서울 강남")
                if collected_info["business_type"] != "미확인":
                    parts = collected_info["business_type"].split()
                    if len(parts) >= 2:
                        collected_info["location"] = " ".join(parts[:-1])  # 마지막 단어(업종) 제외
                
                # USER_CONTEXTS에 영구 저장 (세션 삭제되어도 유지)
                USER_CONTEXTS[session_key] = collected_info
                print(f"💾 수집된 정보 저장 (USER_CONTEXTS): {collected_info}")
                print("➡️  다음 대화는 GUEST_AD_GENERATION 모드로 시작됩니다")
            
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
            
            # Vision 통합: 광고 생성 완료 + 제품 이미지 존재 시
            if (
                intent in [ConversationIntent.AD_GENERATION, ConversationIntent.GUEST_AD_GENERATION]
                and response.final_content
                and "product_image" in CONVERSATION_MEMORIES[session_key]
                and CONVERSATION_MEMORIES[session_key]["product_image"]
            ):
                try:
                    print("🔍 Vision 분석 시작...")
                    
                    # 1. 전략 제안 추출
                    strategy_proposal = extract_last_strategy_proposal(conversation_history)
                    
                    if strategy_proposal:
                        print(f"✅ 전략 제안 추출 성공: {strategy_proposal[:100]}...")
                        
                        # 2. Vision으로 상세 프롬프트 생성
                        product_image_base64 = CONVERSATION_MEMORIES[session_key]["product_image"]
                        business_info = {
                            "business_type": user_context.get("business_type", "미확인") if user_context else "미확인",
                            "location": user_context.get("location", "미확인") if user_context else "미확인",
                            "menu_items": user_context.get("menu_items", "미확인") if user_context else "미확인"
                        }
                        
                        enhanced_prompt = await generate_detailed_image_prompt_with_vision(
                            strategy_proposal=strategy_proposal,
                            product_image_base64=product_image_base64,
                            business_info=business_info
                        )
                        
                        # 3. image_prompt 교체
                        if enhanced_prompt:
                            # Pydantic 모델 업데이트
                            updated_final_content = response.final_content.model_copy(
                                update={"image_prompt": enhanced_prompt}
                            )
                            response = response.model_copy(
                                update={"final_content": updated_final_content}
                            )
                            print("✅ Vision 프롬프트 적용 완료")
                    else:
                        print("⚠️  전략 제안을 찾을 수 없음 (Vision 스킵)")
                        
                except Exception as e:
                    print(f"❌ Vision 통합 실패 (기본 프롬프트 유지): {e}")
        
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
        "bgm_prompt는 MusicGen 같은 음악 생성 모델에서 바로 사용할 수 있는 영어 문장으로 생성해야 함. "
        "bgm_prompt에는 반드시 다음 요소가 모두 포함되어야 함: "
        "장르(genre), 분위기(mood), 템포(tempo 또는 BPM), 주요 악기(instruments), "
        "사용 맥락(context: 예를 들어 small cafe, hair salon, casual restaurant 등)."       
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
      "image_prompt": "Stable Diffusion용 영어 프롬프트",
      "bgm_prompt": "warm lo-fi hip hop instrumental, cozy and relaxed mood, 80-90 BPM, soft piano and light drums, background music for a small neighborhood cafe"
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
        bgm_prompt = data.get("bgm_prompt", "").strip() # 새로 추가 : bgm 프롬프트

        if not isinstance(hashtags, list):
            hashtags = []
        # 7) 최소 필수값 점검 역할
        if not image_prompt:
            # image_prompt 누락 시 캡션/아이디어 기반 기본 프롬프트 생성 보정 역할
            fallback = "clean promotional poster, high quality, modern typography"
            image_prompt = f"{caption or idea}, {fallback}"
        if not bgm_prompt:
            bgm_prompt = (
                "warm lo-fi hip hop instrumental, cozy and relaxed mood, "
                "80-90 BPM, soft piano and light drums, "
                "background music for a small neighborhood cafe"
            )
        else:
            if len(bgm_prompt.split()) < 5:
                bgm_prompt = (
                    "warm lo-fi hip hop instrumental, cozy and relaxed mood, "
                    "80-90 BPM, soft piano and light drums, "
                    "background music for a small neighborhood cafe"          
                )

        return {
            "idea": idea,
            "caption": caption,
            "hashtags": hashtags,
            "image_prompt": image_prompt,
            "bgm_prompt": bgm_prompt,
        }

    except Exception as e:
        # 8) 최종 예외 단일화 및 상위 레이어 전달 역할
        raise ValueError(f"GPT 생성 실패: {e}")

def extract_last_strategy_proposal(conversation_history: list) -> Optional[str]:
    """
    대화 히스토리에서 마지막 전략 제안 텍스트 추출
    (사용자에게 보여준 5가지 전략 - 승인 전)
    
    Args:
        conversation_history: [{"role": "user"|"assistant", "content": str}, ...]
    
    Returns:
        전략 제안 텍스트 (5가지 항목 포함) 또는 None
    """
    if not conversation_history:
        return None
    
    # 역순으로 탐색 (최근 메시지부터)
    for msg in reversed(conversation_history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            
            # 5가지 전략 키워드 확인
            if "메인 메시지" in content and "타겟 고객" in content:
                # 전략 제안 부분만 추출 (1. ~ 5. 포함)
                match = re.search(
                    r'(1\.\s*\*\*메인 메시지\*\*.*?5\.\s*\*\*주요 요소\*\*.*?)(?=\n\n|$)',
                    content,
                    re.DOTALL
                )
                if match:
                    return match.group(1).strip()
                else:
                    # 매칭 실패 시 전체 content 반환 (fallback)
                    return content
    
    return None


async def generate_detailed_image_prompt_with_vision(
    strategy_proposal: str,
    product_image_base64: str,
    business_info: dict
) -> str:
    """
    GPT-4o Vision을 사용하여 제품 이미지 분석 + 전략 기반 상세 프롬프트 생성
    
    Args:
        strategy_proposal: 5가지 전략 제안 텍스트
        product_image_base64: 제품 이미지 (base64 인코딩)
        business_info: 사업자 정보 (업종, 위치 등)
    
    Returns:
        Stable Diffusion용 상세 영어 프롬프트
    """
    print("-------strategy_proposal:----------\n", strategy_proposal)
    try:
        # Vision API 호출용 프롬프트 (단순화 버전)
        vision_prompt = f"""
You are a professional product photography director specializing in commercial advertising.

=== Important Context ===
The product in the image you see will be EXTRACTED and COMPOSITED onto a new background scene.
Your task is to create a Stable Diffusion prompt that describes the BACKGROUND SCENE where this product will be placed.

=== Business Information ===
Business Type: {business_info.get('business_type', 'unknown')}

=== Approved Marketing Strategy ===
{strategy_proposal}

=== Task ===
1. Analyze the product image (color, texture, shape, details)
2. Based on the strategy's "Visual Concept" and "Image Style", design a background scene
3. Create a detailed Stable Diffusion prompt in the following structure

=== Required Prompt Structure (ALL IN ENGLISH) ===

**Part 1: Environment & Atmosphere**
- Setting that matches the strategy's visual concept
- Lighting (warm, soft, dramatic, natural, golden hour)
- Overall mood and atmosphere

**Part 2: Background Elements**
- People, objects, decorations matching target audience
- Specify "in the background, slightly out of focus" or "blurred background"

**Part 3: Photography Style**
- "cinematic photography", "commercial photography", "professional product advertising"
- "shallow depth of field", "bokeh effect"

**Part 4: Product Placement**
- Describe the product you see in the image (be specific about what you observe)
- Must include: "in the foreground", "on the table", "sharp and detailed", "product hero shot"

=== Example Output ===
"A cozy winter cafe interior with warm, soft lighting and large windows,
several people sitting and chatting in the background, slightly out of focus,
cinematic photography, shallow depth of field, professional product advertising,
the new seasonal drink on the table in the foreground, sharp and detailed, product hero shot"

=== Critical Rules ===
- ONLY write the prompt in English (NO Korean, NO explanations)
- Background description comes FIRST
- Product description comes LAST (foreground)
- Background must be "out of focus" or "blurred"
- Product must be "sharp", "detailed", "foreground"
-Do not exceed 77 tokens

Now analyze the product image and generate the prompt:
        """.strip()
        
        # GPT-4o Vision API 호출
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{product_image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        enhanced_prompt = response.choices[0].message.content.strip()
        
        # === 실패 판정 로직 ===
        
        # 1. 거부 메시지 감지
        rejection_words = ["sorry", "can't", "cannot", "unable"]
        if any(word in enhanced_prompt.lower() for word in rejection_words):
            print(f"⚠️  Vision API 거부 감지: {enhanced_prompt[:100]}")
            raise ValueError("Vision API content policy rejection")
        
        # 2. 너무 짧은 응답 (15단어 미만)
        word_count = len(enhanced_prompt.split())
        if word_count < 15:
            print(f"⚠️  응답이 너무 짧음: {word_count}단어")
            raise ValueError(f"Vision API response too short: {word_count} words")
        
        # === 성공: 토큰 검증 및 반환 ===
        
        estimated_tokens = int(word_count * 1.3)  # 보수적 추정
        
        if estimated_tokens > 77:
            print(f"⚠️  프롬프트가 너무 김 ({estimated_tokens} 토큰 추정), 잘라냄")
            # 단어 수 기준으로 자르기 (77토큰 ≈ 60단어)
            words = enhanced_prompt.split()[:60]
            enhanced_prompt = " ".join(words)
        
        print(f"✅ Vision 분석 완료 ({estimated_tokens} 토큰 추정): {enhanced_prompt}")
        
        return enhanced_prompt
        
    except Exception as e:
        print(f"❌ Vision API 실패: {e}")
        # Fallback: strategy_proposal 기반 프롬프트 생성
        print("🔄 Fallback: strategy_proposal로 이미지 프롬프트 생성 시도...")
        
        try:
            fallback_prompt = f"""
Create a Stable Diffusion prompt for product advertising based on this marketing strategy.

Business Type: {business_info.get('business_type', 'unknown')}

Marketing Strategy:
{strategy_proposal}

Generate a detailed prompt following this format:
"[environment with lighting], [background elements, blurred], cinematic photography, shallow depth of field, product in foreground, sharp and detailed"

Requirements:
- Write in English only
- Maximum 77 tokens
- Include background scene description
- Specify "blurred background" or "out of focus"
- End with "product in foreground, sharp and detailed"

Your prompt:
            """.strip()
            
            fallback_response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": fallback_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            fallback_enhanced = fallback_response.choices[0].message.content.strip()
            
            # Fallback도 동일한 검증 적용
            rejection_words = ["sorry", "can't", "cannot", "unable"]
            if any(word in fallback_enhanced.lower() for word in rejection_words):
                print(f"⚠️  Fallback도 거부됨: {fallback_enhanced[:100]}")
                raise ValueError("Fallback also rejected")
            
            word_count = len(fallback_enhanced.split())
            if word_count < 15:
                print(f"⚠️  Fallback 응답이 너무 짧음: {word_count}단어")
                raise ValueError(f"Fallback response too short: {word_count} words")
            
            # 77토큰 제한 검증
            estimated_tokens = int(word_count * 1.3)
            if estimated_tokens > 77:
                print(f"⚠️  Fallback 프롬프트가 너무 김 ({estimated_tokens} 토큰), 잘라냄")
                words = fallback_enhanced.split()[:60]
                fallback_enhanced = " ".join(words)
            
            print(f"✅ Fallback 프롬프트 생성 성공 ({estimated_tokens} 토큰): {fallback_enhanced}")
            return fallback_enhanced
            
        except Exception as fallback_error:
            print(f"❌ Fallback도 실패: {fallback_error}")
            # 최종 기본값
            default_fallback = f"Professional product photography for {business_info.get('business_type', 'business')}, cinematic lighting, blurred background, sharp product in foreground, high quality commercial style"
            print(f"⚠️  최종 기본값 사용: {default_fallback}")
            return default_fallback


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
