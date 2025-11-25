# segmentation.py

# 입력받은 이미지에서 제품 누끼 따기

import os
import torch
import numpy as np
import cv2
from PIL import Image

from mobile_sam import sam_model_registry as mobile_sam_registry
from mobile_sam.automatic_mask_generator import SamAutomaticMaskGenerator
from segment_anything import sam_model_registry, SamPredictor

# =========================================================
# 1. SAM + MobileSAM 로딩
# =========================================================
class ProductSegmentation:
    def __init__(self,
                 mobile_sam_path="backend/weights/mobile_sam.pt",
                 sam_model_type="vit_h",):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.mobile_sam = mobile_sam_registry["vit_t"](checkpoint=mobile_sam_path)
        self.mobile_sam.to(self.device)
        self.mobile_sam.eval()

        self.mask_gen = SamAutomaticMaskGenerator(
            self.mobile_sam,
            points_per_side=24,
        )

        sam_ckpt = os.getenv("SAM_MODEL_PATH")
        if sam_ckpt is None or not os.path.isfile(sam_ckpt):
            raise FileNotFoundError("SAM 모델 체크포인트 파일을 찾을 수 없습니다.")

        sam_model = sam_model_registry[sam_model_type](checkpoint=sam_ckpt)
        sam_model.to(self.device)
        sam_model.eval()

        self.sam_predictor = SamPredictor(sam_model)

    # =========================================================
    # 2. PUBLIC API — 최종 누끼 (MobileSAM + SAM Refinement)
    # =========================================================
    def remove_background(self, image: Image.Image):
        img_rgb = np.array(image.convert("RGB"))

        # MobileSAM → rough mask
        rough_mask = self._mobilesam_segment(img_rgb)

        # SAM Box Prompt refinement
        refined_mask = self._refine_with_sam(img_rgb, rough_mask)

        # RGBA cutouts
        rgba_mobile = self._create_cutout(img_rgb, rough_mask)
        rgba_refined = self._create_cutout(img_rgb, refined_mask)

        """
        return {
            "mobile_mask": rough_mask,
            "refined_mask": refined_mask,
            "mobile_cutout": rgba_mobile,
            "refined_cutout": rgba_refined,
        }
        """
        return refined_mask, rgba_refined

    # =========================================================
    # 3. MobileSAM segmentation
    # =========================================================
    def _mobilesam_segment(self, img_np):
        masks = self.mask_gen.generate(img_np)
        if len(masks) == 0:
            raise ValueError("MobileSAM이 마스크를 감지하지 못했습니다.")

        # area 기준 정렬 → 가장 큰 객체 선택
        masks = sorted(masks, key=lambda x: x["area"], reverse=True)
        mask = masks[0]["segmentation"].astype(np.uint8)

        # inversion 보정
        if mask_needs_invert(mask):
            mask = 1 - mask

        # 경계 부드럽게
        mask = refine_mask(mask)

        return mask

    # =========================================================
    # 4. SAM(Box Prompt) refinement
    # =========================================================
    def _refine_with_sam(self, img_np, mask):
        bbox = self._mask_to_bbox(mask)

        self.sam_predictor.set_image(img_np)
        masks, scores, _ = self.sam_predictor.predict(
            box=bbox,
            multimask_output=True
        )
        best_mask = masks[np.argmax(scores)].astype(np.uint8)

        # inversion 체크
        if mask_needs_invert(best_mask):
            best_mask = 1 - best_mask

        return best_mask

    # =========================================================
    # 5. 유틸 — mask → bounding box
    # =========================================================
    @staticmethod
    def _mask_to_bbox(mask):
        ys, xs = np.where(mask == 1)
        y1, y2 = ys.min(), ys.max()
        x1, x2 = xs.min(), xs.max()
        return np.array([x1, y1, x2, y2])

    # =========================================================
    # 6. 유틸 — RGBA cutout 생성
    # =========================================================
    @staticmethod
    def _create_cutout(img_np, mask):
        rgba = np.dstack([img_np, (mask * 255).astype(np.uint8)])
        return Image.fromarray(rgba)


# =============================================================
# 7. inversion 체크
# =============================================================
def mask_needs_invert(mask):
    h, w = mask.shape
    y1, y2 = int(h * 0.3), int(h * 0.7)
    x1, x2 = int(w * 0.3), int(w * 0.7)

    center = mask[y1:y2, x1:x2]
    ratio = np.mean(center)

    return ratio < 0.3  # 비정상 → 반전 필요


# =============================================================
# 8. 경계 부드럽게
# =============================================================
def refine_mask(mask, blur_size=13):
    mask = (mask * 255).astype(np.uint8)
    mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)
    return (mask.astype(np.float32) / 255.0)