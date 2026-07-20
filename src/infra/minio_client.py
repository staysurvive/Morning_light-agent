"""MinIO object storage adapter used by the knowledge module."""

import io
from dataclasses import dataclass

from minio import Minio

from src.core.config import get_settings


settings = get_settings()

_minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


@dataclass(frozen=True)
class BucketUsage:
    object_count: int
    size_bytes: int


def get_minio_client() -> Minio:
    """Return the shared MinIO client instance."""

    return _minio_client


def ensure_bucket_exists() -> bool:
    """Create the configured bucket when it does not already exist."""

    if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
        _minio_client.make_bucket(settings.MINIO_BUCKET)
    return True


def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload bytes and return the object name stored in the database."""

    _minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type or "application/octet-stream",
    )
    return object_name


def download_file(object_name: str) -> bytes:
    """Download an object as bytes."""

    response = _minio_client.get_object(settings.MINIO_BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_object(object_name: str) -> None:
    """Delete an object from the configured bucket."""

    _minio_client.remove_object(settings.MINIO_BUCKET, object_name)


def get_bucket_usage() -> BucketUsage:
    """Return recursive object count and total object bytes for the bucket."""

    count = 0
    size = 0
    for item in _minio_client.list_objects(settings.MINIO_BUCKET, recursive=True):
        count += 1
        size += int(item.size or 0)
    return BucketUsage(object_count=count, size_bytes=size)
