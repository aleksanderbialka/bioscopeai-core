from bioscopeai_core.app.models.classification import ClassificationResult
from bioscopeai_core.app.schemas.classification import (
    ClassificationResultOut,
)


class ClassificationResultSerializer:
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
