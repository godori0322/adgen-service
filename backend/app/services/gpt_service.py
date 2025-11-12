# gpt_service.py
# OpenAI API를 이용해 입력된 텍스트를 기반으로 홍보 아이디어와 문구, 이미지 생성용 프롬프트 출력

import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_marketing_idea(prompt_text: str, context=None):
    full_prompt = f"""
    아래 입력을 바탕으로 소상공인을 위한 홍보 콘텐츠를 JSON 형태로 생성해줘.

    입력:
    - 사용자 요청: {prompt_text}
    - 맥락 정보: {context or '날씨, 업종, 분위기 등'}

    출력(JSON 형식으로만):
    {{
        "idea": "짧은 이벤트 아이디어 문장",
        "caption": "홍보용 문구 (짧고 감성적인 문장)",
        "hashtags": ["#예시", "#홍보"],
        "image_prompt": "stable diffusion용 영어 프롬프트"
    }}
    """
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.7
    )
    content = res.choices[0].message.content.strip()

    try:
        result = json.loads(content)
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