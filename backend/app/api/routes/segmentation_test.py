# segmentation_test.py

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image
import io

from h11 import PRODUCT_ID

from backend.app.services.segmentation import ProductSegmentation

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