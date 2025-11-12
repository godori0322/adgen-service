# gpt_service.py
# OpenAI API를 이용해 입력된 텍스트를 기반으로 홍보 아이디어와 문구, 이미지 생성용 프롬프트 출력

# import os
# import json
# from openai import OpenAI

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def generate_marketing_idea(prompt_text: str, context=None):
#     full_prompt = f"""
#     아래 입력을 바탕으로 소상공인을 위한 홍보 콘텐츠를 JSON 형태로 생성해줘.

#     입력:
#     - 사용자 요청: {prompt_text}
#     - 맥락 정보: {context or '날씨, 업종, 분위기 등'}

#     출력(JSON 형식으로만):
#     {{
#         "idea": "짧은 이벤트 아이디어 문장",
#         "caption": "홍보용 문구 (짧고 감성적인 문장)",
#         "hashtags": ["#예시", "#홍보"],
#         "image_prompt": "stable diffusion용 영어 프롬프트"
#     }}
#     """
#     res = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": full_prompt}],
#         temperature=0.7
#     )
#     # content = res.choices[0].message.content.strip()
#     content = content.replace("```json", "").replace("```", "").strip()
#     # JSON 파싱 시도

#     try:
#         result = json.loads(content)
#     except json.JSONDecodeError:
#         result = {"idea": content, "caption": content, "hashtags": [], "image_prompt": ""}
#     return result



#-----------------------------------------------------------------------
# gpt_service.py

import os
import json
import re  # 정규식 사용 목적
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        raise ValueError(f"JSON 파싱 실패: {e}. 원문: {text[:300]}...")  # 과도한 로그 방지 목적

def generate_marketing_idea(prompt_text: str, context=None) -> dict:
    """
    - 마케팅 아이디어/캡션/해시태그/이미지 프롬프트 생성 역할
    - 출력 스키마를 JSON으로 강제 및 안전 파싱 역할
    """
    # 1) 시스템 지시문 구성 역할
    system = (
        "너는 소상공인 마케팅 도우미 역할. "
        "항상 JSON 오브젝트만 출력. 코드블록/설명/추가 문장 금지."
    )

    # 2) 사용자 프롬프트 구성 역할
    user = f"""
    아래 입력을 바탕으로 소상공인을 위한 홍보 콘텐츠를 JSON 형태로 생성해줘.

    입력:
    - 사용자 요청: {prompt_text}
    - 맥락 정보: {context or '날씨, 업종, 분위기 등'}

    출력(JSON 오브젝트만, 추가 텍스트/코드블록 금지):
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


