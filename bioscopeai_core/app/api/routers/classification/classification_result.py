from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.classification import (
    ClassificationResultCRUD,
    get_classification_result_crud,
)
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas.classification import (
    ClassificationResultOut,
)
from bioscopeai_core.app.serializers.classification import (
    ClassificationResultSerializer,
    get_classification_result_serializer,
)


classification_result_router = APIRouter()


@classification_result_router.get(
    "/", response_model=list[ClassificationResultOut], status_code=status.HTTP_200_OK
)
async def list_results(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationResultCRUD, Depends(get_classification_result_crud)],
    serializer: Annotated[
        ClassificationResultSerializer,
        Depends(get_classification_result_serializer),
    ],
    classification_id: Annotated[UUID | None, Query()] = None,
    image_id: Annotated[UUID | None, Query()] = None,
) -> list[ClassificationResultOut]:
    """List classification results filtered by image or classification job."""
    results = await crud.get_filtered(
        classification_id=classification_id,
        image_id=image_id,
    )
    return serializer.to_out_list(results)


@classification_result_router.get(
    "/{result_id}",
    response_model=ClassificationResultOut,
    status_code=status.HTTP_200_OK,
)
async def get_result(
    result_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationResultCRUD, Depends(get_classification_result_crud)],
    serializer: Annotated[
        ClassificationResultSerializer,
        Depends(get_classification_result_serializer),
    ],
) -> ClassificationResultOut:
    """Retrieve a single classification result."""
    item = await crud.get_by_id(result_id)
    if not item:
        raise HTTPException(status_code=404, detail="ClassificationResult not found")
    return serializer.to_out(item)


@classification_result_router.get(
    "/classification/{classification_id}",
    response_model=list[ClassificationResultOut],
    status_code=status.HTTP_200_OK,
)
async def get_results_for_classification(
    classification_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationResultCRUD, Depends(get_classification_result_crud)],
    serializer: Annotated[
        ClassificationResultSerializer,
        Depends(get_classification_result_serializer),
    ],
) -> list[ClassificationResultOut]:
    """Return all results for a specific classification job."""
    results = await crud.get_by_classification(classification_id)
    return serializer.to_out_list(results)


@classification_result_router.get(
    "/image/{image_id}",
    response_model=list[ClassificationResultOut],
    status_code=status.HTTP_200_OK,
)
async def get_results_for_image(
    image_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    crud: Annotated[ClassificationResultCRUD, Depends(get_classification_result_crud)],
    serializer: Annotated[
        ClassificationResultSerializer,
        Depends(get_classification_result_serializer),
    ],
) -> list[ClassificationResultOut]:
    """Return all results for a specific image."""
    results = await crud.get_by_image(image_id)
    return serializer.to_out_list(results)
