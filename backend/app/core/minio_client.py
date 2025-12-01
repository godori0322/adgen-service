from minio import Minio
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "adgen_minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin1234")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False") == "True"

BUCKET_IMAGE = os.getenv("MINIO_BUCKET_IMAGE", "adgen-images")
BUCKET_VIDEO = os.getenv("MINIO_BUCKET_VIDEO", "adgen-videos")
BUCKET_AUDIO = os.getenv("MINIO_BUCKET_AUDIO", "adgen-audio")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# 필요한 버킷 자동 생성
for bucket in [BUCKET_IMAGE, BUCKET_VIDEO, BUCKET_AUDIO]:
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
