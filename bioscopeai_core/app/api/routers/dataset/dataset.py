from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bioscopeai_core.app.models.dataset import Dataset

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.dataset import DatasetCRUD, get_dataset_crud
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas.dataset import (
    DatasetCreate,
    DatasetMinimalOut,
    DatasetOut,
    DatasetUpdate,
)
from bioscopeai_core.app.serializers.dataset import (
    DatasetSerializer,
    get_dataset_serializer,
)


dataset_router = APIRouter()


@dataset_router.get(
    "/",
    response_model=list[DatasetOut],
    status_code=status.HTTP_200_OK,
)
async def list_datasets(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    dataset_crud: Annotated[DatasetCRUD, Depends(get_dataset_crud)],
    dataset_serializer: Annotated[DatasetSerializer, Depends(get_dataset_serializer)],
) -> list[DatasetOut]:
    datasets: list[Dataset] = await dataset_crud.get_user_datasets(user)
    return dataset_serializer.to_out_list(datasets, user)


@dataset_router.post(
    "/",
    response_model=DatasetMinimalOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset(
    dataset_in: DatasetCreate,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    dataset_crud: Annotated[DatasetCRUD, Depends(get_dataset_crud)],
    dataset_serializer: Annotated[DatasetSerializer, Depends(get_dataset_serializer)],
) -> DatasetMinimalOut:
    dataset: Dataset = await dataset_crud.create_for_user(dataset_in, user)
    return dataset_serializer.to_minimal(dataset)


@dataset_router.get(
    "/{dataset_id}",
    response_model=DatasetOut,
    status_code=status.HTTP_200_OK,
)
async def get_dataset(
    dataset_id: str,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    dataset_crud: Annotated[DatasetCRUD, Depends(get_dataset_crud)],
    dataset_serializer: Annotated[DatasetSerializer, Depends(get_dataset_serializer)],
) -> DatasetOut:
    dataset = await dataset_crud.get_by_id_for_user(dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset_serializer.to_out(dataset, user)


@dataset_router.patch(
    "/{dataset_id}",
    response_model=DatasetOut,
    status_code=status.HTTP_200_OK,
)
async def update_dataset(
    dataset_id: str,
    dataset_in: DatasetUpdate,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    dataset_crud: Annotated[DatasetCRUD, Depends(get_dataset_crud)],
    dataset_serializer: Annotated[DatasetSerializer, Depends(get_dataset_serializer)],
) -> DatasetOut:
    updated = await dataset_crud.update_dataset(dataset_id, dataset_in, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset_serializer.to_out(updated, user)


@dataset_router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: str,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    dataset_crud: Annotated[DatasetCRUD, Depends(get_dataset_crud)],
) -> None:
    deleted = await dataset_crud.delete_by_id_for_user(dataset_id, user)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
