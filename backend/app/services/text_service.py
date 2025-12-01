# text_service.py

# Diffusion 파이프라인에서 전달받은 제품 + 배경 합성 이미지에, 
# 사용자가 원하는 텍스트를 템플릿에 맞춰 삽입 후 반환하는 모듈
from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
from pathlib import Path
from typing import Tuple
import unicodedata
import re


class TextService:
    def __init__(self):
        self.font_dir = Path("/home/shared/fonts")
        font_config_path = self.font_dir / "font_config.json"
        print("[FONT CONFIG] Load attempt:", font_config_path)

        # JSON 로드 시 예외 처리 추가 (실패 원인 로그 출력)
        try:
            if font_config_path.exists():
                with open(font_config_path, "r", encoding="utf-8") as f:
                    self.font_map = json.load(f)
                print("[FONT CONFIG] Loaded:", self.font_map)
            else:
                print("[FONT CONFIG] NOT FOUND → fallback 사용")
                self.font_map = {}
        except Exception as e:
            print("[FONT CONFIG ERROR]", e)
            self.font_map = {}

        # fallback 기본값
        self.font_map.setdefault("regular", "/home/shared/fonts/NotoSansKR-Regular.ttf")
        self.font_map.setdefault("bold", "/home/shared/fonts/NotoSansKR-Bold.ttf")
        self.default_font_path = self.font_map.get("default", self.font_map["regular"])

        print("[FONT MAP FINAL]", self.font_map)

    # 이모지 판별 함수
    def is_emoji(self, char: str) -> bool: 
        return unicodedata.category(char) in ["So", "Sk"]

    # ---------------------------------------------------------
    # 텍스트 삽입 메인 함수
    # ---------------------------------------------------------
    def add_text(
        self,
        image: Image.Image,
        text: str,
        mode: str = "bottom",
        font_mode: str = "regular",
        font_size_ratio: float = 0.06,
        color: Tuple[int, int, int] = (255, 255, 255),
        max_width_ratio: float = 0.8,
        line_spacing_ratio: float = 1.4,
    ) -> Image.Image:
        """
        Diffusion 최종 이미지에 텍스트 삽입.

        Args:
            image (PIL.Image): 배경 + 제품 합성된 최종 이미지
            text (str): 추가할 문자열
            mode (str): top / middle / bottom
            font_path (str): 폰트 경로
            color (Tuple): RGB 색상
        """
        draw = ImageDraw.Draw(image)
        W, H = image.size

        # Main font
        font_name = self.font_map.get(font_mode, self.default_font_path)
        font_path = Path(font_name)
        if not font_path.is_absolute():
            font_path = self.font_dir / font_path

        print("[FONT SELECT] mode=", font_mode, "path=", font_path)
        
        font_size = int(H * font_size_ratio)
        font_main = ImageFont.truetype(str(font_path), max(int(H * font_size_ratio), 20))

        # Emoji font
        emoji_font_path = self.font_dir / "NotoEmoji-Regular.ttf"
        try:
            font_emoji = ImageFont.truetype(str(emoji_font_path), font_size)
        except Exception as e:
            print("[Emoji Font Load Failed → fallback to main font]", e)
            font_emoji = font_main

        max_width = int(W * max_width_ratio)
        lines = self._wrap_text(draw, text, font_main, max_width)

        base_height = font_main.getbbox("A")[3] - font_main.getbbox("A")[1]
        line_height = int(base_height * line_spacing_ratio)
        total_height = line_height * len(lines)

        # ---------------------------------------------------------
        # 위치 계산(고정 마진이 아닌, 이미지 크기에 따른 가변적인 텍스트 위치 조정)
        # ---------------------------------------------------------
        top_margin = int(H * 0.05)
        bottom_margin = int(H * 0.07)
        
        if mode == "top":
            y = top_margin
        elif mode == "middle":
            y = (H - total_height) // 2
        else:
            y = H - total_height - bottom_margin

        # ---------------------------------------------------------
        # 텍스트 렌더링 (그림자 적용해 자연스러운 스타일)
        # ---------------------------------------------------------
        for i, line in enumerate(lines):
            offset_x = (W - draw.textlength(line, font=font_main)) // 2

            for char in line:
                current_font = font_emoji if self.is_emoji(char) else font_main  
                bbox = current_font.getbbox(char)
                w = bbox[2] - bbox[0]

                # 그림자 + 본문
                draw.text((offset_x + 2, y + i * line_height + 2), char, font=current_font, fill=(0, 0, 0))
                draw.text((offset_x    , y + i * line_height    ), char, font=current_font, fill=color)

                offset_x += w

        return image

    # ---------------------------------------------------------
    # 줄바꿈 처리 함수
    # ---------------------------------------------------------
    def _wrap_text(self, draw, text, font, max_width):
        """
        1단계: , . ! ? 뒤에서 강제 줄바꿈 힌트 넣기
        2단계: 그 줄 안에서만 max_width 기준으로 다시 줄바꿈
        """
        # 쉼표 뒤에서 줄바꿈 힌트 넣기
        # "크리스마스, 행복한 하루!" -> "크리스마스,\n행복한 하루!\n"
        text = re.sub(r'([,])\s*', r'\1\n', text)

        paragraphs = text.split("\n")  # 구두점 기준으로 미리 쪼갠 문장들
        lines: list[str] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            words = para.split()  # 이 안에서는 다시 단어 단위로 줄바꿈
            current = ""

            for w in words:
                test = f"{current} {w}" if current else w
                if draw.textlength(test, font=font) <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = w

            if current:
                lines.append(current)

        return lines