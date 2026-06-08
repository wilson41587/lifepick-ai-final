import os
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "lifepick-files")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def ensure_bucket():
    """Create bucket if it does not exist."""
    found = minio_client.bucket_exists(MINIO_BUCKET)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET)


def upload_file_to_minio(local_path: Path, object_name: str) -> str:
    """
    Upload local file to MinIO.
    Return storage path string.
    """
    ensure_bucket()

    minio_client.fput_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_name,
        file_path=str(local_path),
    )

    return f"minio://{MINIO_BUCKET}/{object_name}"


def delete_file_from_minio(storage_path: str):
    """
    Delete file from MinIO by storage path.
    Expected format: minio://bucket/object_name
    """
    if not storage_path or not storage_path.startswith("minio://"):
        return

    path = storage_path.replace("minio://", "", 1)
    parts = path.split("/", 1)

    if len(parts) != 2:
        return

    bucket, object_name = parts

    try:
        minio_client.remove_object(bucket, object_name)
    except S3Error:
        # Demo version: ignore missing object.
        pass
