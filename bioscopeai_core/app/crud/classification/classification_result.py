from collections import Counter
from datetime import datetime, timedelta, UTC
from typing import Any
from uuid import UUID

from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models.classification import ClassificationResult
from bioscopeai_core.app.schemas.classification import (
    ClassificationResultCreate,
)


class ClassificationResultCRUD(BaseCRUD[ClassificationResult]):
    model = ClassificationResult

    async def create_result(
        self,
        data: ClassificationResultCreate,
    ) -> ClassificationResult:
        obj: ClassificationResult = await self.model.create(
            image_id=data.image_id,
            classification_id=data.classification_id,
            label=data.label,
            confidence=data.confidence,
            model_name=data.model_name,
        )
        return obj

    async def get_filtered(
        self,
        classification_id: UUID | None = None,
        image_id: UUID | None = None,
    ) -> list[ClassificationResult]:
        filters = {
            "classification_id": classification_id,
            "image_id": image_id,
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        classification_results: list[ClassificationResult] = await self.model.filter(
            **filters
        ).order_by("-created_at")

        return classification_results

    async def get_by_classification(
        self, classification_id: UUID
    ) -> list[ClassificationResult]:
        return await self.get_filtered(classification_id=classification_id)

    async def get_by_image(self, image_id: UUID) -> list[ClassificationResult]:
        return await self.get_filtered(image_id=image_id)

    async def get_today_statistics(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        date_range: datetime = now - timedelta(days=1)
        classification_results: list[ClassificationResult] = await self.model.filter(
            created_at__gte=date_range,
        ).order_by("-created_at")

        count: int = len(classification_results)
        confidence: float = (
            sum(result.confidence for result in classification_results) / count
            if count > 0
            else 0.0
        )

        hourly_counts: Counter[str] = Counter(
            result.created_at.replace(minute=0, second=0, microsecond=0).strftime(
                "%Y-%m-%dT%H:00:00Z"
            )
            for result in classification_results
        )

        hourly_data: list[dict[str, int | str]] = [
            {
                "hour": (
                    hour_str := (now - timedelta(hours=i))
                    .replace(minute=0, second=0, microsecond=0)
                    .strftime("%Y-%m-%dT%H:00:00Z")
                ),
                "count": hourly_counts[hour_str],
            }
            for i in range(24, -1, -1)
        ]

        return {
            "classified_last_24_hours": count,
            "average_confidence": confidence,
            "last_10_results": classification_results[:10],
            "hourly_counts": hourly_data,
        }


def get_classification_result_crud() -> ClassificationResultCRUD:
    return ClassificationResultCRUD()
