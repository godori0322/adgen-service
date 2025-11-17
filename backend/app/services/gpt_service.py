# gpt_service.py
# generat_marketing_idae 함수 유지
# langchain 사용 _get_or_create_chain, generate_conversation_response 함수 추가

import os
import json
import re  # 정규식 사용 목적
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.app.core.schemas import DialogueGPTResponse, FinalContentSchema

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# langchain 변수 정의
CONVERSATION_MEMORIES = {}  # session_id -> ConversationChain 매핑
MAX_MEMORY_TURNS = 5
parser = PydanticOutputParser(pydantic_object=DialogueGPTResponse)

# Multi-turn 대화 관리 및 다음 질문 생성 역할 : 대화 목표, 응답 형식 지시
DIALOGUE_TEMPLATE = """
너는 소상공인 마케팅 도우미 역할을 한다.
너의 목표는 '업종', '홍보 목적', '메뉴/제품명', '원하는 분위기', '특별한 행사/이벤트' 정보를 수집하고, 수집이 완료되면 최종 콘텐츠를 생성하는 것이다.

{user_info}

현재 대화 기록:
{history}

사용자의 새로운 입력에 대해 다음 JSON 형식으로 응답해야 한다.
{format_instructions}

사용자: {input}
AI 응답:
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

        
       

# ================== Multi-turn lanchain 대화 관리 함수 ==================
def _get_or_create_chain(session_id: str, user_context: dict = None):
    """특정 session_id에 대한 langchain conversatiochain을 가져오거나 생성"""
    if session_id not in CONVERSATION_MEMORIES:
        # 사용자 정보를 프롬프트에 반영
        user_info = ""
        if user_context:
            info_parts = []
            if user_context.get("business_type"):
                info_parts.append(f"업종: {user_context['business_type']} (이미 알고 있음, 다시 묻지 마)")
            if user_context.get("location"):
                info_parts.append(f"위치: {user_context['location']}")
            if user_context.get("menu_items"):
                info_parts.append(f"메뉴/제품: {user_context['menu_items']} (이미 알고 있음, 다시 묻지 마)")
            if user_context.get("business_hours"):
                info_parts.append(f"영업시간: {user_context['business_hours']}")
            
            if info_parts:
                user_info = "사용자 정보 (이미 알고 있는 정보, 다시 묻지 말 것):\n" + "\n".join(info_parts)
        
        # LangChain LLM 설정
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # 메모리 설정 (MAX_MEMORY_TURNS 만큼 기억)
        memory = ConversationBufferWindowMemory(
            k=MAX_MEMORY_TURNS,
            memory_key="history"
        )
        
        # 프롬프트 구성
        prompt = PromptTemplate(
            template=DIALOGUE_TEMPLATE,
            input_variables=["input"], # history는 memory가 관리
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "user_info": user_info if user_info else "사용자 정보 없음 (모든 정보를 질문해야 함)"
            },
        )

        # Conversation Chain 생성 및 저장
        chain = ConversationChain(
            llm=llm,
            prompt=prompt,
            memory=memory,
            verbose=False 
        )
        # LLM, Memory, Pydantic Output Parser, Prompt Template 설정 후 Chain 생성
        CONVERSATION_MEMORIES[session_id] = chain
    return CONVERSATION_MEMORIES[session_id]

def generate_conversation_response(session_id: str, user_input: str, user_context: dict = None) -> DialogueGPTResponse:
    """langchain 사용해서 multi-turn 대화 응답 생성"""
    try:
        chain = _get_or_create_chain(session_id, user_context)
        # langchain 실행(메모리 자동 관리 & 프롬프트 주입)
        raw_response = chain.invoke(input=user_input)['response'].strip()
        # Pydantic 모델로 변환 & 유효성 검사
        data = _safe_json_from_text(raw_response)
        return DialogueGPTResponse(**data)

    except Exception as e:
        if session_id in CONVERSATION_MEMORIES:
            del CONVERSATION_MEMORIES[session_id]
        raise ValueError(f"LangChain 대화 응답 생성 실패: {e}")


      
# 단일 콘텐츠 생성
def generate_marketing_idea(prompt_text: str, context=None) -> dict:
    """
    [기존 기능 유지] 단일 턴에서 마케팅 아이디어 생성하는 역할
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
        res = client.chat.completions.create(
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

        
    # 도시명 변환(정규화)
    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        json_str = match.group()
    else:
        json_str = content

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        result = {"idea": content, "caption": content, "hashtags": [], "image_prompt": ""}
    return result

def extract_city_name_english(location: str) -> str:
    """
    한글 지역명을 GPT를 사용하여 영어 도시명으로 변환
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
        
        res = client.chat.completions.create(
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
