import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import cast
from uuid import UUID

import anyio
from fastapi import HTTPException, UploadFile
from loguru import logger

from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models import Dataset, Image
from bioscopeai_core.app.schemas.image import ImageCreate, ImageUpdate


ALLOWED_ORDER_FIELDS = {"uploaded_at", "filename", "created_at"}


class ImageCRUD(BaseCRUD[Image]):
    model = Image

    async def get_filtered_images(
        self,
        dataset_id: UUID | None = None,
        device_id: UUID | None = None,
        uploaded_by: UUID | None = None,
        analyzed: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        q: str | None = None,
        order_by: str = "-uploaded_at",
        page: int = 1,
        page_size: int = 25,
    ) -> list[Image]:
        """Retrieve images with optional filtering, pagination, and sorting."""
        order_field = order_by.lstrip("-")
        if order_field not in ALLOWED_ORDER_FIELDS:
            raise HTTPException(status_code=400, detail="Invalid order_by field")

        filters = {
            "dataset_id": dataset_id,
            "device_id": device_id,
            "uploaded_by_id": uploaded_by,
            "analyzed": analyzed,
            "uploaded_at__gte": created_from,
            "uploaded_at__lte": created_to,
            "filename__icontains": q,
        }
        # Drop None values
        filters = {k: v for k, v in filters.items() if v is not None}

        query = self.model.filter(**filters).order_by(order_by)
        offset: int = (page - 1) * page_size
        images: list[Image] = await query.offset(offset).limit(page_size)
        return images

    async def create_image(
        self, image_in: ImageCreate, uploaded_by_id: UUID, uploaded_file: UploadFile
    ) -> Image:
        """Create a new image record and save the uploaded file."""

        await self._validate_file(uploaded_file)
        # Save to dataset subdirectory for better organization
        try:
            dataset: Dataset = await Dataset.get(id=image_in.dataset_id).only("name")
        except Exception as e:
            logger.exception("Failed to retrieve dataset for image upload")
            raise HTTPException(status_code=400, detail="Invalid dataset ID") from e
        try:
            dataset_dir = Path(settings.image.UPLOAD_DIR) / self._clean_name(
                dataset.name
            )
            await anyio.Path(str(dataset_dir)).mkdir(exist_ok=True, parents=True)
            filename = uploaded_file.filename or f"{uuid.uuid4()}"
            filepath = str(dataset_dir / filename)
            async with await anyio.open_file(filepath, "x+b") as f:
                await f.write(await uploaded_file.read())
        except FileExistsError as e:
            logger.exception(f"File already exists at {filepath}")
            raise HTTPException(status_code=409, detail="File already exists") from e
        except OSError as e:
            logger.error(f"OS error while saving file: {e}")
            raise HTTPException(status_code=500, detail="Filesystem error") from e
        except Exception as e:
            logger.exception("Failed to save uploaded file")
            raise HTTPException(status_code=500, detail="File upload failed") from e
        logger.info(
            f"User {uploaded_by_id} uploaded {uploaded_file.filename} -> {filepath}"
        )
        try:
            obj: Image = await self.model.create(
                filename=uploaded_file.filename,
                filepath=filepath,
                dataset_id=image_in.dataset_id,
                uploaded_by_id=uploaded_by_id,
                device_id=image_in.device_id,
            )
            logger.info(f"Image record created in DB: {obj.id}")
        except Exception as e:
            logger.exception("Failed to create image record in database")
            try:
                await anyio.Path(filepath).unlink()
                logger.info(f"Deleted orphaned file: {filepath}")
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.exception(
                    f"Failed to delete orphaned file {filepath}: {cleanup_exc}"
                )
            raise HTTPException(
                status_code=500, detail="Image record creation failed"
            ) from e

        return obj

    async def update_image(self, image_id: UUID, image_in: ImageUpdate) -> Image | None:
        """Update an existing image record."""

        image = await self.model.get_or_none(id=image_id)
        if not image:
            logger.info(f"Image {image_id} not found for update")
            return None

        update_data = image_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(image, field, value)

        try:
            await image.save()
            await image.refresh_from_db()
            logger.info(f"Image {image_id} updated")
        except Exception as e:
            logger.exception("Failed to update image record")
            raise HTTPException(status_code=500, detail="Image update failed") from e

        return cast("Image", image)

    @staticmethod
    async def _validate_file(uploaded_file: UploadFile) -> None:
        """Validate the uploaded file for MIME type, extension, and size."""

        # Validate MIME type
        if uploaded_file.content_type not in settings.image.ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Invalid file type")
        if uploaded_file.filename is None:
            raise HTTPException(status_code=400, detail="Filename is missing")
        # Validate file extension
        ext = Path(uploaded_file.filename).suffix.lower()
        if ext not in settings.image.ALLOWED_EXT:
            raise HTTPException(status_code=400, detail="Invalid file extension")
        # Validate size and empty file
        contents = await uploaded_file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="File is empty")
        if len(contents) > settings.image.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        await uploaded_file.seek(0)

    @staticmethod
    def _clean_name(name: str) -> str:
        """
        Cleans the dataset name by replacing whitespace with underscores and trimming.
        """
        return re.sub(r"\s+", "_", name.strip())


def get_image_crud() -> ImageCRUD:
    """Returns an instance of ImageCRUD."""
    return ImageCRUD()
