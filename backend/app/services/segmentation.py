# segmentation.py

# 입력받은 이미지에서 제품 누끼 따기

import torch
import numpy as np
import cv2
from PIL import Image

from mobile_sam import sam_model_registry
from mobile_sam.automatic_mask_generator import SamAutomaticMaskGenerator

class MobileSAMSegmentation:
    def __init__(self, model_type="vit_t", checkpoint_path="weights/mobile_sam.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = sam_model_registry[model_type](checkpoint=checkpoint_path)
        self.model.to(self.device)
        self.model.eval()
        self.mask_generator = SamAutomaticMaskGenerator(self.model)

    def remove_background(self, image: Image.Image):
        # PIL -> numpy 변환(RGB)
        img_rgb = np.array(image.convert("RGB"))

        # 자동 마스크 제네레이터
        masks = self.mask_generator.generate(img_rgb)

        # 가장 큰 마스크(제품) 1개 선택
        if len(masks) == 0:
            raise ValueError("No Mask found by SAM")
    
        masks_sorted = sorted(masks, key=lambda x: x["area"], reverse=True)
        mask = masks_sorted[0]["segmentation"].astype(np.uint8)

        if mask_needs_invert(img_rgb, mask):
            mask = 1 - mask

        mask = refine_mask(mask)

        # 누끼 따기 위한 RGB -> RGBA 이미지 생성
        rgba = np.dstack([img_rgb, (mask * 255).astype(np.uint8)])
        cutout = Image.fromarray(rgba)

        return mask, cutout

# MobileSAM의 AutoMaskGenerator는 "제품:1, 배경:0" 마스킹이 항상 보장 X
# 조명이 강하거나 제품과 배경 구분이 명확하지 않은 경우 mask 반전 위험 있음
# 제품과 배경의 평균 색상 비교, mask polarity 자동 판별
def mask_needs_invert(img_rgb, mask):
    fg = img_rgb[mask == 1]
    bg = img_rgb[mask == 0]

    fg_var = np.var(fg)
    bg_var = np.var(bg)

    return fg_var < bg_var 

# 마스킹 후처리: 경계선을 자연스럽게 보정
def refine_mask(mask, blur_size=15):
    mask = (mask * 255).astype(np.uint8)
    refined = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
    refined = refined / 255.0
    return refined