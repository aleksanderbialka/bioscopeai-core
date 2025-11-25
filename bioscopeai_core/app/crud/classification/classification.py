from typing import Any
from uuid import UUID

from loguru import logger

from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.kafka.producers.classification_producer import (
    ClassificationJobProducer,
    get_classification_producer,
)
from bioscopeai_core.app.models.classification import (
    Classification,
    ClassificationStatus,
)
from bioscopeai_core.app.schemas.classification import ClassificationCreate


class ClassificationCRUD(BaseCRUD[Classification]):
    model = Classification

    async def create_job(
        self,
        created_by_id: UUID,
        create_in: ClassificationCreate,
    ) -> Classification:
        obj: Classification = await self.model.create(
            dataset_id=create_in.dataset_id,
            image_id=create_in.image_id,
            model_name=create_in.model_name,
            created_by_id=created_by_id,
            status=ClassificationStatus.PENDING,
        )
        classification_job_producer: ClassificationJobProducer = (
            get_classification_producer()
        )
        try:
            await classification_job_producer.send_event(
                device_id=str(created_by_id),
                message={
                    "classification_id": str(obj.id),
                    "dataset_id": str(create_in.dataset_id)
                    if create_in.dataset_id
                    else None,
                    "image_id": str(create_in.image_id) if create_in.image_id else None,
                    "model_name": create_in.model_name or None,
                },
            )
        except Exception:
            await self.set_status(
                status=ClassificationStatus.FAILED,
                classification_id=obj.id,
            )
            logger.exception(
                f"Failed to send classification job to Kafka for classification ID {obj.id}"
            )
            raise

        return obj

    async def set_status(
        self,
        status: ClassificationStatus,
        classification_id: UUID,
    ) -> Classification | None:
        obj: Classification | None = await self.model.get_or_none(id=classification_id)
        if obj is None:
            return None
        obj.status = status
        await obj.save()

        return obj

    async def get_filtered(
        self,
        status: str | None = None,
        dataset_id: UUID | None = None,
        image_id: UUID | None = None,
        created_by: UUID | None = None,
    ) -> list[Classification]:
        filters: dict[str, Any] = {
            "status": ClassificationStatus(status) if status else None,
            "dataset_id": dataset_id,
            "image_id": image_id,
            "created_by_id": created_by,
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        classifications: list[Classification] = await self.model.filter(
            **filters
        ).order_by("-created_at")

        return classifications


def get_classification_crud() -> ClassificationCRUD:
    return ClassificationCRUD()
