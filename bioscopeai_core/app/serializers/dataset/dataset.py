from bioscopeai_core.app.models import Dataset
from bioscopeai_core.app.schemas.dataset import (
    DatasetMinimalOut,
    DatasetOut,
)


class DatasetSerializer:
    @staticmethod
    def to_out(dataset: Dataset) -> DatasetOut:
        return DatasetOut(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            owner_username=dataset.owner.username,
            created_at=dataset.created_at,
        )

    @staticmethod
    def to_out_list(datasets: list[Dataset]) -> list[DatasetOut]:
        return [DatasetSerializer.to_out(d) for d in datasets]

    @staticmethod
    def to_minimal(dataset: Dataset) -> DatasetMinimalOut:
        return DatasetMinimalOut(
            id=dataset.id,
            name=dataset.name,
        )


def get_dataset_serializer() -> DatasetSerializer:
    return DatasetSerializer()
