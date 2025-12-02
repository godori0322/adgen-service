# segmentation.py
# SAM 단독으로 입력받은 이미지에서 제품 누끼 따기

# .env 로드 (SAM_MODEL_PATH 사용)
from dotenv import load_dotenv
load_dotenv()

import os
import threading
import torch
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import base64

from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator

_segmentation_singleton = None

class ProductSegmentation:
    def __init__(
        self,
        sam_model_type: str = "vit_b",
        sam_max_size: int = 768,   # SAM 입력 최대 해상도(긴 변 기준, 필요 시 사용)
        points_per_side: int = 24, # 자동 마스크 생성 정밀도 (필요시 조절)
        upscaler_scale: int = 2,
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sam_model_type = sam_model_type
        self.sam_max_size = sam_max_size
        self.points_per_side = points_per_side
        self.upscale_factor = upscaler_scale

        # lazy loading용 플레이스홀더
        self.sam_model = None
        self.sam_predictor = None
        self.mask_gen = None

        self._load_lock = threading.Lock()

    # =========================================================
    # 1. SAM 모델 로드 (Lazy Load)
    # =========================================================
    def _ensure_models_loaded(self):
        if self.sam_model is not None:
            return

        with self._load_lock:
            if self.sam_model is not None:
                return

            sam_ckpt = os.getenv("SAM_MODEL_PATH")
            if sam_ckpt is None or not os.path.isfile(sam_ckpt):
                raise FileNotFoundError("SAM_MODEL_PATH 환경변수를 통해 SAM 체크포인트 파일을 찾을 수 없습니다.")

            print(f"[Segmentation] Loading SAM ({self.sam_model_type}) from {sam_ckpt}")

            # SAM 모델 로드
            sam_model = sam_model_registry[self.sam_model_type](checkpoint=sam_ckpt)
            sam_model.to("cuda")
            sam_model.eval()

            # Predictor (원하면 point/box prompt 용으로 사용 가능)
            self.sam_predictor = SamPredictor(sam_model)

            # SAM 전용 AutomaticMaskGenerator 사용
            self.mask_gen = SamAutomaticMaskGenerator(
                sam_model,
                points_per_side=self.points_per_side,
                pred_iou_thresh=0.88,
                stability_score_thresh=0.9,
                crop_n_layers=1,
                crop_n_points_downscale_factor=2,
                min_mask_region_area=200,  # 작은 노이즈 제거
            )

            self.sam_model = sam_model
            print("[Segmentation] SAM 모델 및 자동 마스크 제너레이터 로드 완료.")

    # =========================================================
    # 2. PUBLIC API — 최종 누끼 (SAM 단독)
    # =========================================================
    def remove_background(self, image: Image.Image):
        """
        SAM만 사용해서:
        1) 자동 마스크 생성
        2) 가장 큰 객체의 마스크 선택
        3) RGBA 컷아웃 생성

        return:
            refined_mask (np.ndarray, 0~1 float)
            rgba_cutout (PIL.Image, RGBA)
        """
        self._ensure_models_loaded()

        img_rgb = np.array(image.convert("RGB"))

        # SAM의 AutomaticMaskGenerator로 마스크 후보 생성
        masks = self.mask_gen.generate(img_rgb)
        if len(masks) == 0:
            raise ValueError("SAM이 마스크를 감지하지 못했습니다.")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        # 종합 점수 기준으로 가장 제품일 확률이 높은 마스크 선정
        best_mask = select_best_mask(img_rgb, masks)

        # inversion 체크 (중앙이 비어 있으면 반전)
        if mask_needs_invert(best_mask):
            best_mask = 1 - best_mask

        # 경계 부드럽게 (0~1 float)
        refined_mask = refine_mask(best_mask)

        # halo 제거
        refined_mask = remove_halo(refined_mask)

        # RGBA 컷아웃 생성
        rgba_refined = self._create_cutout(img_rgb, refined_mask)

        # 색상 decontamination
        rgba_np = np.array(rgba_refined)[..., :3]
        cleaned = color_decontaminate(rgba_np, refined_mask)

        # numpy -> PIL
        rgb_cutout = Image.fromarray(cleaned)
        alpha = (refined_mask * 255).astype(np.uint8)
        rgba_cutout = np.dstack([cleaned, alpha])
        rgba_final = Image.fromarray(rgba_cutout)

        return refined_mask, rgba_final

    # =========================================================
    # 3. 유틸 — RGBA cutout 생성
    # =========================================================
    @staticmethod
    def _create_cutout(img_np: np.ndarray, mask_float: np.ndarray) -> Image.Image:
        """
        img_np: H x W x 3 (RGB, uint8)
        mask_float: H x W (0~1 float)
        """
        alpha = np.clip(mask_float * 255.0, 0, 255).astype(np.uint8)
        rgba = np.dstack([img_np, alpha])
        return Image.fromarray(rgba)

# -------------------------------------------------------------
# Singleton instance (서버 실행 시 한 번만 실행, 동일 인스턴스 사용)
# -------------------------------------------------------------
def get_segmentation_singleton():
    global _segmentation_singleton
    if _segmentation_singleton is None:
        _segmentation_singleton = ProductSegmentation()
        _segmentation_singleton._ensure_models_loaded()
    return _segmentation_singleton

# =============================================================
# 4. inversion 체크
# =============================================================
def mask_needs_invert(mask: np.ndarray) -> bool:
    """
    마스크 중앙 부분이 대부분 0이면 (배경으로 판단되면) 반전 필요하다고 판단.
    """
    if mask.ndim == 3:
        mask = mask[..., 0]

    h, w = mask.shape

    # 중앙 40% 영역 체크
    y1, y2 = int(h * 0.3), int(h * 0.7)
    x1, x2 = int(w * 0.3), int(w * 0.7)

    center_ratio = np.mean(mask[y1:y2, x1:x2])

    # 전체 픽셀 중 마스크 비율
    fg_ratio = np.mean(mask)

    # 조건 1: 중앙이 비어 있음 (기존 로직)
    cond1 = center_ratio < 0.3

    # 조건 2: 거의 전체가 마스크 (배경 전체 감지한 경우)
    cond2 = fg_ratio > 0.85

    return cond1 or cond2


# =============================================================
# 5. 경계 부드럽게
# =============================================================
def refine_mask(mask: np.ndarray, blur_size: int = 13) -> np.ndarray:
    """
    mask: 0/1 (uint8 또는 bool)
    return: 0~1 float mask (blur 적용)
    """
    mask = (mask * 255).astype(np.uint8)
    mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
    return (mask.astype(np.float32) / 255.0)

# =============================================================
# 6. 경계의 halo 제거
# =============================================================
def remove_halo(mask_float: np.ndarray, erode_size=3, blur_size=7):
    """
    SAM이 만든 mask_float(0-1)을 입력받아 halo 제거 후 반환
    """
    mask = (mask_float * 255).astype(np.uint8)

    # 1) erode로 경계 침식
    kernel = np.ones((erode_size, erode_size), np.uint8)
    eroded = cv2.erode(mask, kernel, iterations=1)

    # 2) soft blur로 자연스럽게 보정
    cleaned = cv2.GaussianBlur(eroded, (blur_size, blur_size), 0)

    # 3) 0-1 스케일 복구
    return cleaned.astype(np.float32) / 255.0

# =============================================================
# 7. 색상 decontamination
# =============================================================
def color_decontaminate(img_np, mask_float, strength=0.6):
    """
    img_np: HXW RGB
    mask_float: 0-1 mask
    strength: 0-1 (0: 원본 유지, 1: 완전 decontaminate)
    """
    mask_expanded = np.clip(mask_float + 0.15, 0, 1)
    blurred_img = cv2.GaussianBlur(img_np, (11, 11), 0)

    decont = img_np * mask_expanded[..., None] + blurred_img * (1 - mask_expanded[..., None]) * strength
    return decont.astype(np.uint8)

# =============================================================
# best mask 선택 유틸
# =============================================================

# =============================================================
# 1. 마스크의 중심도(centeredness)
# =============================================================
def mask_center_score(mask):
    h, w = mask.shape
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0
    
    cx, cy = xs.mean(), ys.mean()
    dx = abs(cx - w / 2) / (w / 2)
    dy = abs(cy - h / 2) / (h / 2)
    dist = (dx + dy) / 2
    # 중앙에 가까울수록 점수가 높음
    return 1 - dist

# =============================================================
# 2. 마스크 내부 평균 색상 분산(color variance)
# =============================================================
def color_variance_score(img, mask):
    masked = img[mask > 0]
    if len(masked) == 0:
        return 0
    var = np.var(masked)
    return min(var / 5000, 1.0)

# =============================================================
# 3. 마스크 경계 복잡도(edge complexity)
# =============================================================
def edge_complex_score(mask):
    edges = cv2.Canny((mask * 255).astype(np.uint8), 50, 150)
    score = edges.sum() / 255
    return min(score / 5, 1.0)

# =============================================================
# 4. 종합 점수 계산
# =============================================================
def select_best_mask(img_rgb, masks):
    h, w, _ = img_rgb.shape
    best_score = -1e9
    best_mask = None

    for m in masks:
        mask = m["segmentation"]
        if mask.ndim == 3:
            mask = mask[..., 0]
        mask = mask.astype(np.uint8)

        area = m["area"]
        area_ratio = area / (h * w)

        # 너무 작거나 너무 큰 영역(배경일 확률 높음) 제거
        if area_ratio < 0.01 or area_ratio > 0.9:
            continue

        # 1) 중앙 정렬 점수
        center_score = mask_center_score(mask)

        # 2) 색상 다양성
        color_var_score = color_variance_score(img_rgb, mask)

        # 3) 경계 복잡도
        edge_score = edge_complex_score(mask)

        # 4) 경계에 닿아 있는 마스크 패널티
        ys, xs = np.where(mask > 0)
        if len(xs) > 0:
            border_touch = (
                np.mean(xs < w * 0.05) +
                np.mean(xs > w * 0.95) +
                np.mean(ys < h * 0.05) +
                np.mean(ys > h * 0.95)
            )
        else:
            border_touch = 4

        border_penalty = min(border_touch, 1.0)

        # 최종 스코어
        total_score = (
            0.45 * center_score +
            0.30 * edge_score +
            0.05 * color_var_score +
            0.10 * area_ratio -
            0.20 * border_penalty
        )

        if total_score > best_score:
            best_score = total_score
            best_mask = mask

    if best_mask is None:
        # fallback: 가장 큰 마스크라도 사용
        best_mask = max(masks, key=lambda x: x["area"])["segmentation"]

    return best_mask

# =============================================================
# 5. 누끼 미리 보여주는 함수
# =============================================================
def preview_segmentation(original_image: Image.Image) -> dict:
    """
    원본 이미지를 입력받아:
    - mask_array
    - cutout (투명 배경)
    - overlay (원본 위에 마스크 반투명 오버레이)
    를 생성해서 Base64로 반환
    """
    model = get_segmentation_singleton()

    mask_array, cutout_image = model.remove_background(original_image)
    mask_image = _mask_array_to_pil(mask_array)

    # 1) cutout PNG (RGBA)
    cutout_rgba = cutout_image.convert("RGBA")
    buf_cutout = BytesIO()
    cutout_rgba.save(buf_cutout, format="PNG")
    cutout_b64 = base64.b64encode(buf_cutout.getvalue()).decode("utf-8")

    # 2) overlay: 원본 위에 마스크를 반투명 색으로 칠하기
    overlay = original_image.convert("RGBA")
    overlay_mask = mask_image.resize(original_image.size).convert("L")

    color_layer = Image.new("RGBA", overlay.size, (0, 255, 0, 120))  # 연한 초록 계열
    overlay = Image.composite(color_layer, overlay, overlay_mask)

    buf_overlay = BytesIO()
    overlay.save(buf_overlay, format="PNG")
    overlay_b64 = base64.b64encode(buf_overlay.getvalue()).decode("utf-8")

    # 3) 품질 heuristic
    H, W = mask_array.shape
    area_ratio = mask_array.sum() / (H * W)
    # 너무 작거나 너무 크면 warning
    if area_ratio < 0.02:
        quality = "too_small"
    elif area_ratio > 0.85:
        quality = "too_big"
    else:
        quality = "ok"

    return {
        "cutout_b64": cutout_b64,
        "overlay_b64": overlay_b64,
        "area_ratio": area_ratio,
        "quality": quality,
    }

def _mask_array_to_pil(mask_array: np.ndarray) -> Image.Image:
    """SAM 마스크(ndarray)를 흑백(L) 모드 PIL 이미지로 변환."""
    scaled = np.clip(mask_array * 255.0, 0, 255).astype("uint8")
    return Image.fromarray(scaled, mode="L")