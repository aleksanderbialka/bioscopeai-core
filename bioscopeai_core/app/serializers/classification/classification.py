from bioscopeai_core.app.models.classification import Classification
from bioscopeai_core.app.schemas.classification import (
    ClassificationMinimalOut,
    ClassificationOut,
)


class ClassificationSerializer:
    @staticmethod
    def to_out(obj: Classification) -> ClassificationOut:
        return ClassificationOut(
            id=obj.id,
            dataset_id=obj.dataset_id,
            image_id=obj.image_id,
            model_name=obj.model_name,
            status=obj.status,
            created_by_id=obj.created_by_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    @staticmethod
    def to_minimal(obj: Classification) -> ClassificationMinimalOut:
        return ClassificationMinimalOut(
            id=obj.id,
            status=obj.status,
        )

    def to_out_list(self, objs: list[Classification]) -> list[ClassificationOut]:
        return [self.to_out(o) for o in objs]


def get_classification_serializer() -> ClassificationSerializer:
    return ClassificationSerializer()
