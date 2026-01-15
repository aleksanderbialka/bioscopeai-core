from __future__ import annotations

from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from bioscopeai_core.app.core.config import settings


@lru_cache(maxsize=1)
def get_s3_client() -> Any:
    """Get a cached S3 client instance configured for MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=settings.minio.ENDPOINT_URL,
        aws_access_key_id=settings.minio.ACCESS_KEY,
        aws_secret_access_key=settings.minio.SECRET_KEY.get_secret_value(),
    )


def ensure_bucket_exists(bucket: str | None = None) -> None:
    """Ensure that the specified S3 bucket exists; create it if it does not."""
    s3 = get_s3_client()
    bucket_name = bucket or settings.minio.DEFAULT_BUCKET

    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as exc:
        code = (exc.response.get("Error") or {}).get("Code", "")
        if code in {"404", "NoSuchBucket", "NotFound"}:
            logger.info("Bucket '{}' does not exist. Creating it...", bucket_name)
        else:
            logger.exception("Cannot head_bucket for '{}': {}", bucket_name, code)
            raise
    else:
        return
    try:
        s3.create_bucket(Bucket=bucket_name)
        logger.info("Bucket '{}' created.", bucket_name)
    except ClientError as exc:
        code = (exc.response.get("Error") or {}).get("Code", "")
        if code in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            return
        logger.exception("Failed to create bucket '{}': {}", bucket_name, code)
        raise
