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

# 이미지 전처리
def preprocess_for_sam(img_rgb):
    img = img_rgb.copy()

    # L 채널(명도) 대비 향상(LAB: RGB보다 밝기에 초점을 둔 색 공간)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    # CLAHE(Contrast Limited Adaptive Histogram Equalization) 전처리
    # 국소 대비 향상을 위한 알고리즘 -> 대비 강화, 노이즈 제거
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)

    lab = cv2.merge((l2, a, b))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # Gamma Correction(조명 보정)
    gamma = 1.1
    img = np.power(img / 255.0, gamma)
    img = np.uint8(img * 255)

    # Sharpening(경계 강화)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    img = cv2.filter2D(img, -1, kernel)

    return img

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