# diffusion_service.py
# 입력받은 프롬프트를 바탕으로 홍보용 이미지 출력 (GPU 미사용 - 플레이스홀더 이미지 반환)

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import random


def generate_poster_image(prompt: str, product_image_bytes: Optional[bytes] = None) -> bytes:
    """
    GPU를 사용하지 않고 임의의 플레이스홀더 이미지를 생성합니다.
    팀원들과 GPU 공유 시 충돌을 피하기 위한 임시 구현입니다.
    
    Args:
        prompt: 이미지 생성용 프롬프트
        product_image_bytes: 제품 이미지 바이트 (선택사항)
    """
    try:
        prompt = str(prompt).encode("utf-8", errors="ignore").decode("utf-8")
        print(f"[PLACEHOLDER] generating placeholder image for prompt: {prompt}")
        
        if product_image_bytes:
            print(f"[PLACEHOLDER] product image received: {len(product_image_bytes)} bytes")

        # 512x512 크기의 이미지 생성 (랜덤 배경색)
        colors = [
            (255, 182, 193),  # 연한 핑크
            (173, 216, 230),  # 연한 파랑
            (144, 238, 144),  # 연한 초록
            (255, 218, 185),  # 복숭아색
            (221, 160, 221),  # 연한 보라
            (255, 250, 205),  # 레몬색
        ]
        bg_color = random.choice(colors)
        
        # 이미지 생성
        image = Image.new('RGB', (512, 512), color=bg_color)
        draw = ImageDraw.Draw(image)
        
        # product_image가 있으면 합성 (간단한 예시)
        if product_image_bytes:
            try:
                product_img = Image.open(BytesIO(product_image_bytes))
                # 제품 이미지를 작게 리사이즈
                product_img.thumbnail((200, 200))
                # 중앙 하단에 붙이기
                x = (512 - product_img.width) // 2
                y = 512 - product_img.height - 50
                image.paste(product_img, (x, y))
            except Exception as e:
                print(f"[WARNING] Failed to process product image: {e}")
        
        # 테두리 추가
        border_color = tuple(max(0, c - 50) for c in bg_color)
        draw.rectangle([10, 10, 502, 502], outline=border_color, width=5)
        
        # 텍스트 추가 (중앙에 "Generated Image" 표시)
        try:
            # 시스템 기본 폰트 사용
            font = ImageFont.load_default()
        except:
            font = None
        
        text = "🎨 Generated Image"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (512 - text_width) // 2
        text_y = (512 - text_height) // 2 - 50
        
        draw.text((text_x, text_y), text, fill=(60, 60, 60), font=font)
        
        # 프롬프트 일부 표시 (짧게)
        prompt_display = prompt[:40] + "..." if len(prompt) > 40 else prompt
        prompt_bbox = draw.textbbox((0, 0), prompt_display, font=font)
        prompt_width = prompt_bbox[2] - prompt_bbox[0]
        prompt_x = (512 - prompt_width) // 2
        prompt_y = text_y + 30
        
        draw.text((prompt_x, prompt_y), prompt_display, fill=(80, 80, 80), font=font)

        # PNG로 변환
        buf = BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        raise RuntimeError(f"Placeholder image generation error: {e}")
