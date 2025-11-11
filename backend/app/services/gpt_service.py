# gpt_service.py
# OpenAI API를 이용해 입력된 텍스트를 기반으로 홍보 아이디어와 문구, 이미지 생성용 프롬프트 출력

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_marketing_idea(prompt_text: str, context=None):
    full_prompt = f"""
    사용자 요청: {prompt_text}
    맥락: {context or "오늘의 날씨, 업종 정보를 기반으로"}
    필요한 출력: 
    1. 이벤트 아이디어
    2. 광고 문구
    3. 이미지 생성용 프롬프트
    """
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}]
    )
    return res.choices[0].message.content