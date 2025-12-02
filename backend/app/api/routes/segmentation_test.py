# segmentation_test.py

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
import io

from h11 import PRODUCT_ID

from backend.app.services.segmentation import ProductSegmentation
from backend.app.services.segmentation import preview_segmentation

router = APIRouter(prefix="/segmentation_test", tags=["Segmentation"])

model = ProductSegmentation()

@router.post("/remove_bg", response_class=StreamingResponse, responses={200: {"content": {"image/png": {}}}})
async def remove_bg(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    mask, cutout = model.remove_background(img)

    cutout_rgb = cutout.convert("RGB")
    cutout_mask = cutout.getchannel("A")  # 알파 채널 → 마스크

    w, h = img.size
    combined = Image.new("RGB", (w * 2, h), (255, 255, 255))  # 흰 배경

    combined.paste(img, (0, 0))

    combined.paste(cutout_rgb, (w, 0), mask=cutout_mask)

    output = io.BytesIO()
    combined.save(output, format="PNG")
    output.seek(0)

    return StreamingResponse(output, media_type="image/png")

@router.post("/preview")
async def segmentation_preview(file: UploadFile = File(...)):
    img_bytes = await file.read()
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    result = preview_segmentation(image)

    return JSONResponse(
        {
            "cutout_image": f"data:image/png;base64,{result['cutout_b64']}",
            "overlay_image": f"data:image/png;base64,{result['overlay_b64']}",
            "area_ratio": result["area_ratio"],
            "quality": result["quality"],
            "message": _build_quality_message(result["quality"]),
        }
    )


def _build_quality_message(quality: str) -> str:
    if quality == "too_small":
        return "상품이 화면에서 너무 작게 잡힌 것 같아요. 제품을 화면 중앙에 더 크게 찍어주세요."
    if quality == "too_big":
        return "상품이 화면을 거의 다 채우고 있어서 배경과 구분이 어렵습니다. 약간 뒤로 물러나서 찍어주세요."
    return "상품이 잘 인식된 것 같아요. 결과를 확인해보세요!"