import json
from uuid import UUID

from loguru import logger

from bioscopeai_core.app.models.classification.classification_result import (
    ClassificationResult,
)
from bioscopeai_core.app.schemas.classification import (
    ClassificationResultCreate,
    ClassificationResultOut,
)


class ClassificationResultSerializer:
    @staticmethod
    def create_from_event(
        classification_result_event: str,
    ) -> ClassificationResultCreate:
        try:
            classification_result_data = json.loads(classification_result_event)
        except json.JSONDecodeError:
            logger.exception("Invalid JSON in message: %s", classification_result_event)
        return ClassificationResultCreate(
            image_id=UUID(classification_result_data.get("image_id")),
            classification_id=UUID(classification_result_data.get("classification_id")),
            label=classification_result_data.get("label"),
            confidence=classification_result_data.get("confidence"),
            model_name=classification_result_data.get("model_name"),
        )

    @staticmethod
    def to_out(obj: ClassificationResult) -> ClassificationResultOut:
        return ClassificationResultOut(
            id=obj.id,
            image_id=obj.image_id,
            classification_id=obj.classification_id,
            label=obj.label,
            confidence=obj.confidence,
            model_name=obj.model_name,
            created_at=obj.created_at,
        )

    def to_out_list(
        self, objs: list[ClassificationResult]
    ) -> list[ClassificationResultOut]:
        return [self.to_out(o) for o in objs]


def get_classification_result_serializer() -> ClassificationResultSerializer:
    return ClassificationResultSerializer()
