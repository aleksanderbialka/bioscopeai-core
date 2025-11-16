from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger

from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models import Dataset, User
from bioscopeai_core.app.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetCRUD(BaseCRUD[Dataset]):
    model = Dataset

    async def get_user_datasets(self, user: User) -> list[Dataset]:
        datasets: list[Dataset] = await self.model.filter(owner=user).prefetch_related(
            "owner"
        )
        return datasets

    async def get_by_id_for_user(self, dataset_id: UUID, user: User) -> Dataset | None:
        dataset: Dataset | None = await self.model.get_or_none(
            id=dataset_id, owner=user
        ).prefetch_related("owner")
        return dataset

    async def create_for_user(self, dataset_in: DatasetCreate, user: User) -> Dataset:
        obj: Dataset = await self.model.create(
            **dataset_in.model_dump(),
            owner=user,
        )
        return obj

    async def update_dataset(
        self, dataset_id: UUID, dataset_in: DatasetUpdate, user: User
    ) -> Dataset | None:
        dataset: Dataset | None = await self.model.get_or_none(
            id=dataset_id, owner=user
        ).prefetch_related("owner")
        if not dataset:
            return None

        update_data = dataset_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dataset, field, value)

        await dataset.save()
        await dataset.refresh_from_db()
        return dataset

    async def delete_by_id_for_user(self, obj_id: UUID, user: User) -> bool:
        dataset: Dataset | None = await self.model.get_or_none(id=obj_id)
        if not dataset:
            logger.info(
                f"Dataset {obj_id} not found for deletion by user {user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

        if dataset.owner_id != user.id and not user.is_admin:
            logger.warning(
                f"User {user.id} attempted to delete dataset {obj_id} without permission"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this dataset",
            )

        await dataset.delete()
        logger.info(f"Dataset {obj_id} deleted by user {user.id}")
        return True


def get_dataset_crud() -> DatasetCRUD:
    return DatasetCRUD()
