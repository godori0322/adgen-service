# segmentation_test.py

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image
import io

from backend.app.services.segmentation import MobileSAMSegmentation

router = APIRouter(prefix="/segmentation_test", tags=["Segmentation"])

model = MobileSAMSegmentation(
    model_type="vit_t",
    checkpoint_path="backend/weights/mobile_sam.pt"
)

@router.post("/remove_bg", response_class=StreamingResponse, responses={200: {"content": {"image/png": {}}}})
async def remove_bg(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    mask, cutout = model.remove_background(img)

    output = io.BytesIO()
    cutout.save(output, format="PNG")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="image/png"
    )