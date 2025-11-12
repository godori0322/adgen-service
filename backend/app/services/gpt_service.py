# gpt_service.py
# OpenAI API를 이용해 입력된 텍스트를 기반으로 홍보 아이디어와 문구, 이미지 생성용 프롬프트 출력

import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_marketing_idea(prompt_text: str, context=None):
    full_prompt = f"""
    아래 입력을 바탕으로 소상공인을 위한 홍보 콘텐츠를 JSON 형태로 생성해줘.

    입력:
    - 사용자 요청: {prompt_text}
    - 맥락 정보: {context or '날씨, 업종, 분위기 등'}

    출력(JSON 형식으로만, ``json 블록 없이):
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

    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        json_str = match.group()
    else:
        json_str = content

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        result = {"idea": content, "caption": content, "hashtags": [], "image_prompt": ""}
    
    if not result.get("image_prompt"):
        result["image_prompt"] = "a simple modern poster design, warm mood, product focused"
    
    return result