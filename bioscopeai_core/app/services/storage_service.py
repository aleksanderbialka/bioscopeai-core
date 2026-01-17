from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from loguru import logger

from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.core.s3_client import get_s3_client


class StorageService:
    """Service for managing file storage operations with S3/MinIO."""

    def __init__(self) -> None:
        """Initialize storage service with S3 client."""
        self.s3_client = get_s3_client()
        self.default_bucket = settings.minio.DEFAULT_BUCKET

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        parts = filename.rsplit(".", 1)
        return f".{parts[1]}" if len(parts) > 1 else ""

    @staticmethod
    def fix_presigned_url(url: str) -> str:
        """Replace internal Docker endpoint with public URL in presigned URLs."""
        if not settings.minio.PUBLIC_URL:
            return url
        internal_endpoint: str = settings.minio.ENDPOINT_URL
        if not internal_endpoint.startswith(("http://", "https://")):
            protocol = "https://" if settings.minio.USE_SSL else "http://"
            internal_endpoint = f"{protocol}{internal_endpoint}"
        return url.replace(internal_endpoint, settings.minio.PUBLIC_URL)

    async def upload_file(
        self,
        file: UploadFile,
        bucket: str | None = None,
        object_name: str | None = None,
    ) -> str:
        """Upload file to S3/MinIO."""
        bucket_name = bucket or self.default_bucket

        if not object_name:
            file_extension = self._get_file_extension(file.filename or "file")
            object_name = f"{uuid4()}{file_extension}"

        try:
            contents = await file.read()
            file_obj = BytesIO(contents)

            self.s3_client.upload_fileobj(
                file_obj,
                bucket_name,
                object_name,
                ExtraArgs={
                    "ContentType": file.content_type or "application/octet-stream"
                },
            )

        except ClientError as e:
            logger.exception(f"Failed to upload file to {bucket_name}/{object_name}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {e.response['Error']['Message']}",
            ) from e
        except Exception as e:
            logger.exception(
                f"Unexpected error during file upload: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {e!s}",
            ) from e
        else:
            logger.info(f"Uploaded file to {bucket_name}/{object_name}")
            return object_name
        finally:
            # Reset file pointer for potential reuse
            await file.seek(0)

    async def delete_file(
        self,
        object_name: str,
        bucket: str | None = None,
    ) -> None:
        """Delete file from S3/MinIO."""
        bucket_name = bucket or self.default_bucket
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            logger.info(f"Deleted file from {bucket_name}/{object_name}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.warning(
                    f"File not found for deletion: {bucket_name}/{object_name}"
                )
                return

            logger.exception(f"Failed to delete file from {bucket_name}/{object_name}")
            raise HTTPException(
                status_code=500,
                detail=f"File deletion failed: {e.response['Error']['Message']}",
            ) from e
        except Exception as e:
            logger.exception(
                f"Unexpected error during file deletion: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"File deletion failed: {e!s}",
            ) from e

    async def get_presigned_url(
        self,
        object_name: str,
        bucket: str | None = None,
        expires_in: int = 604800,  # 7 days in seconds
    ) -> str:
        """Generate presigned URL for file access."""
        bucket_name = bucket or self.default_bucket

        try:
            url: str = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_name},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.exception(
                f"Failed to generate presigned URL: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"URL generation failed: {e.response['Error']['Message']}",
            ) from e
        except Exception as e:
            logger.exception(
                f"Unexpected error generating presigned URL: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"URL generation failed: {e!s}",
            ) from e
        else:
            return url

    async def file_exists(
        self,
        object_name: str,
        bucket: str | None = None,
    ) -> bool:
        bucket_name = bucket or self.default_bucket

        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            logger.exception(
                f"Error checking file existence: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"File existence check failed: {e.response['Error']['Message']}",
            ) from e
        except Exception as e:
            logger.exception(
                f"Unexpected error checking file existence: {bucket_name}/{object_name}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"File existence check failed: {e!s}",
            ) from e
        else:
            return True


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    """Get cached storage service instance for dependency injection."""
    return StorageService()
