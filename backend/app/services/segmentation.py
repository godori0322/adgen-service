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

from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator

class ProductSegmentation:
    def __init__(
        self,
        sam_model_type: str = "vit_b",
        sam_max_size: int = 768,   # SAM 입력 최대 해상도(긴 변 기준, 필요 시 사용)
        points_per_side: int = 24, # 자동 마스크 생성 정밀도 (필요시 조절)
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sam_model_type = sam_model_type
        self.sam_max_size = sam_max_size
        self.points_per_side = points_per_side

        # lazy loading용 플레이스홀더
        self.sam_model = None
        self.sam_predictor = None
        self.mask_gen = None

        self._load_lock = threading.Lock()

    # =========================================================
    # 1. SAM 모델 로드 (Lazy Load)
    # =========================================================
    def _ensure_models_loaded(self):
        if self.sam_model is not None and self.mask_gen is not None:
            return

        with self._load_lock:
            if self.sam_model is not None and self.mask_gen is not None:
                return

            sam_ckpt = os.getenv("SAM_MODEL_PATH")
            if sam_ckpt is None or not os.path.isfile(sam_ckpt):
                raise FileNotFoundError("SAM_MODEL_PATH 환경변수를 통해 SAM 체크포인트 파일을 찾을 수 없습니다.")

            print(f"[Segmentation] Loading SAM ({self.sam_model_type}) from {sam_ckpt}")

            # SAM 모델 로드
            sam_model = sam_model_registry[self.sam_model_type](checkpoint=sam_ckpt)
            sam_model.to(self.device)
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

        if torch.cuda.is_available():
            self.sam_model.to("cuda")

        img_rgb = np.array(image.convert("RGB"))

        # SAM의 AutomaticMaskGenerator로 마스크 후보 생성
        masks = self.mask_gen.generate(img_rgb)
        if len(masks) == 0:
            raise ValueError("SAM이 마스크를 감지하지 못했습니다.")

        # area 기준으로 가장 큰 객체 선택
        masks = sorted(masks, key=lambda x: x["area"], reverse=True)
        best = masks[0]
        mask = best["segmentation"].astype(np.uint8)
        mask = np.squeeze(mask)

        # inversion 체크 (중앙이 비어 있으면 반전)
        if mask_needs_invert(mask):
            mask = 1 - mask

        # 경계 부드럽게 (0~1 float)
        refined_mask = refine_mask(mask)

        # RGBA 컷아웃 생성
        rgba_refined = self._create_cutout(img_rgb, refined_mask)

        if torch.cuda.is_available():
            self.sam_model.to("cpu")

            try:
                self.sam_predictor.reset_image()
            except:
                pass

            if hasattr(self.mask_gen, "predictor"):
                self.mask_gen.predictor = None

            del self.mask_gen
            self.mask_gen = None

            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            
            print("[Segmentation] SAM moved back to CPU after segmentation.")

        return refined_mask, rgba_refined

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


# =============================================================
# 4. inversion 체크
# =============================================================
def mask_needs_invert(mask: np.ndarray) -> bool:
    """
    마스크 중앙 부분이 대부분 0이면 (배경으로 판단되면) 반전 필요하다고 판단.
    """
    if mask.ndim == 3:
        mask = mask.squeeze()
    if mask.ndim != 2:
        raise ValueError(f"Invalid mask shape: {mask.shape}")
    
    h, w = mask.shape
    y1, y2 = int(h * 0.3), int(h * 0.7)
    x1, x2 = int(w * 0.3), int(w * 0.7)

    center = mask[y1:y2, x1:x2]
    ratio = np.mean(center)  # 0~1

    return ratio < 0.3  # 중앙부가 비어 있다 → 반전 필요


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
