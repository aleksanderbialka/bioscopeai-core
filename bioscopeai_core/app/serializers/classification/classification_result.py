import json

from loguru import logger

from bioscopeai_core.app.models.classification.classification_result import (
    ClassificationResult,
)
from bioscopeai_core.app.schemas.classification import (
    ClassificationResultCreate,
    ClassificationResultOut,
)


class ClassificationResultSerializer:
    """Serializer for classification result events."""

    @staticmethod
    def create_from_event(
        classification_result_event: str,
    ) -> ClassificationResultCreate:
        try:
            classification_result_data = json.loads(classification_result_event)
        except json.JSONDecodeError as e:
            msg = "Invalid JSON format"
            logger.exception(msg)
            raise ValueError(msg) from e
        return ClassificationResultCreate.model_validate(classification_result_data)

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
