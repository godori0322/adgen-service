import uuid
from io import BytesIO
from backend.app.core.minio_client import (
    minio_client, BUCKET_IMAGE, BUCKET_AUDIO, BUCKET_VIDEO
)

def upload_bytes(file_bytes: bytes, content_type: str) -> str:
    
    # 파일 이름 + 버킷 선택
    if content_type.startswith("image/"):
        bucket = BUCKET_IMAGE
        file_name = f"{uuid.uuid4()}.png"
    elif content_type.startswith("video/"):
        bucket = BUCKET_VIDEO
        file_name = f"{uuid.uuid4()}.mp4"
    else:
        bucket = BUCKET_AUDIO
        file_name = f"{uuid.uuid4()}.wav"

    # 버킷 없으면 생성
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)

    # 파일 업로드
    minio_client.put_object(
        bucket,
        file_name,
        data=BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )

    # 접근 가능한 URL 리턴
    return f"/{bucket}/{file_name}"
