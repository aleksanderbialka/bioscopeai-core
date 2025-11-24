from typing import Annotated, TYPE_CHECKING
from uuid import UUID


if TYPE_CHECKING:
    from bioscopeai_core.app.models.classification.classification import Classification


from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.classification import (
    ClassificationCRUD,
    get_classification_crud,
)
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas.classification import (
    ClassificationCreate,
    ClassificationMinimalOut,
    ClassificationOut,
)
from bioscopeai_core.app.serializers.classification import (
    ClassificationSerializer,
    get_classification_serializer,
)


classification_router = APIRouter()


@classification_router.post(
    "/run",
    response_model=ClassificationMinimalOut,
    status_code=status.HTTP_201_CREATED,
)
async def run_classification(
    request: Request,
    create_in: ClassificationCreate,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationCRUD, Depends(get_classification_crud)],
    serializer: Annotated[
        ClassificationSerializer, Depends(get_classification_serializer)
    ],
) -> ClassificationMinimalOut:
    """
    Start a new classification job for a single image OR an entire dataset.
    Exactly ONE of image_id or dataset_id must be provided.
    """
    # validation — exactly one of image_id / dataset_id
    if bool(create_in.dataset_id) == bool(create_in.image_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of dataset_id or image_id.",
        )

    # Create job + emit event to Kafka
    job: Classification = await crud.create_job(
        created_by_id=user.id,
        create_in=create_in,
    )
    return serializer.to_minimal(job)


@classification_router.get(
    "/", response_model=list[ClassificationOut], status_code=status.HTTP_200_OK
)
async def list_classifications(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationCRUD, Depends(get_classification_crud)],
    serializer: Annotated[
        ClassificationSerializer, Depends(get_classification_serializer)
    ],
    status_filter: Annotated[
        str | None,
        Query(description="Filter by status: pending/running/completed/failed"),
    ] = None,
    dataset_id: Annotated[UUID | None, Query()] = None,
    image_id: Annotated[UUID | None, Query()] = None,
    created_by: Annotated[UUID | None, Query()] = None,
) -> list[ClassificationOut]:
    """Return classifications filtered by dataset, image, user or status."""
    items = await crud.get_filtered(
        status=status_filter,
        dataset_id=dataset_id,
        image_id=image_id,
        created_by=created_by,
    )
    return serializer.to_out_list(items)


@classification_router.get(
    "/{classification_id}",
    response_model=ClassificationOut,
    status_code=status.HTTP_200_OK,
)
async def get_classification(
    classification_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationCRUD, Depends(get_classification_crud)],
    serializer: Annotated[
        ClassificationSerializer, Depends(get_classification_serializer)
    ],
) -> ClassificationOut:
    """Retrieve a single classification job."""
    job = await crud.get_by_id(classification_id)
    if not job:
        raise HTTPException(status_code=404, detail="Classification not found")
    return serializer.to_out(job)


@classification_router.delete(
    "/{classification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_classification(
    classification_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    crud: Annotated[ClassificationCRUD, Depends(get_classification_crud)],
) -> None:
    """Delete a classification job."""
    deleted = await crud.delete_by_id(classification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Classification not found")
