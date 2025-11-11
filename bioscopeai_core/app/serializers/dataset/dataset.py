from bioscopeai_core.app.models import Dataset, User
from bioscopeai_core.app.schemas.dataset import (
    DatasetMinimalOut,
    DatasetOut,
)


class DatasetSerializer:
    @staticmethod
    def to_out(dataset: Dataset, user: User) -> DatasetOut:
        return DatasetOut(
            id=str(dataset.id),
            name=dataset.name,
            description=dataset.description,
            owner_username=user.username,
            created_at=dataset.created_at,
        )

    def to_out_list(self, datasets: list[Dataset], user: User) -> list[DatasetOut]:
        return [self.to_out(d, user) for d in datasets]

    @staticmethod
    def to_minimal(dataset: Dataset) -> DatasetMinimalOut:
        return DatasetMinimalOut(
            id=str(dataset.id),
            name=dataset.name,
        )


def get_dataset_serializer() -> DatasetSerializer:
    return DatasetSerializer()
