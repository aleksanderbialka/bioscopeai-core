import mimetypes
from datetime import datetime
from typing import Annotated
from uuid import UUID

import anyio
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.image import get_image_crud, ImageCRUD
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas.image import (
    ImageCreate,
    ImageMinimalOut,
    ImageOut,
    ImageUpdate,
)
from bioscopeai_core.app.serializers.image import (
    get_image_serializer,
    ImageSerializer,
)


image_router = APIRouter()


@image_router.get("/", response_model=list[ImageOut], status_code=status.HTTP_200_OK)
async def list_images(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
    image_serializer: Annotated[ImageSerializer, Depends(get_image_serializer)],
    dataset_id: Annotated[
        UUID | None, Query(description="Filter by dataset ID")
    ] = None,
    device_id: Annotated[UUID | None, Query(description="Filter by device ID")] = None,
    uploaded_by: Annotated[
        UUID | None, Query(description="Filter by uploader user ID")
    ] = None,
    analyzed: Annotated[
        bool | None, Query(description="Filter by analyzed status")
    ] = None,
    created_from: Annotated[
        datetime | None, Query(description="Uploaded after this date")
    ] = None,
    created_to: Annotated[
        datetime | None, Query(description="Uploaded before this date")
    ] = None,
    q: Annotated[str | None, Query(description="Search in filenames")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 25,
    order_by: Annotated[
        str,
        Query(
            description="Sort by field (e.g. 'uploaded_at', '-uploaded_at', 'filename')",
        ),
    ] = "uploaded_at",
) -> list[ImageOut]:
    """List images with optional filters (dataset, device, uploader, analyzed state),
    date range, full-text search, pagination, and sorting."""

    images = await image_crud.get_filtered_images(
        dataset_id=dataset_id,
        device_id=device_id,
        uploaded_by=uploaded_by,
        analyzed=analyzed,
        created_from=created_from,
        created_to=created_to,
        q=q,
        order_by=order_by,
        page=page,
        page_size=page_size,
    )
    return image_serializer.to_out_list(images)


@image_router.get(
    "/{image_id}",
    response_model=ImageOut,
    status_code=status.HTTP_200_OK,
)
async def get_image(
    image_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
    image_serializer: Annotated[ImageSerializer, Depends(get_image_serializer)],
) -> ImageOut:
    """Get image metadata by ID."""

    image = await image_crud.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image_serializer.to_out(image)


@image_router.post(
    "/upload",
    response_model=ImageMinimalOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
    image_serializer: Annotated[ImageSerializer, Depends(get_image_serializer)],
    dataset_id: Annotated[UUID, Form()],
    device_id: Annotated[UUID | None, Form()] = None,
    file: UploadFile = File(...),  # noqa: B008
) -> ImageMinimalOut:
    """Upload a new image file and create an Image record associated with a dataset."""

    image_in = ImageCreate(
        dataset_id=dataset_id, device_id=device_id, filename=file.filename
    )
    image = await image_crud.create_image(image_in, user.id, file)
    return image_serializer.to_minimal(image)


@image_router.patch(
    "/{image_id}",
    response_model=ImageOut,
    status_code=status.HTTP_200_OK,
)
async def update_image(
    image_id: UUID,
    image_in: ImageUpdate,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
    image_serializer: Annotated[ImageSerializer, Depends(get_image_serializer)],
) -> ImageOut:
    """Update the image with the given ID."""

    updated = await image_crud.update_image(image_id, image_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Image not found")
    return image_serializer.to_out(updated)


@image_router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
) -> None:
    """Delete the image with the given ID."""

    deleted = await image_crud.delete_by_id(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")


@image_router.get(
    "/{image_id}/file",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {"image/*": {}},
            "description": "Returns the image file associated with the given image ID",
        },
        404: {"description": "Image or file not found"},
    },
)
async def get_image_file(
    image_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    image_crud: Annotated[ImageCRUD, Depends(get_image_crud)],
    download: Annotated[bool, Query(description="Force download of the file")] = False,
) -> FileResponse:
    """Retrieve the image file associated with the given image ID.
    Set `download=True` to force file download."""

    image = await image_crud.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if not await anyio.Path(image.filepath).exists():
        raise HTTPException(status_code=404, detail="Image file not found on server")

    mime_type, _ = mimetypes.guess_type(image.filepath)
    mime_type = mime_type or "application/octet-stream"

    disposition = "attachment" if download else "inline"
    headers = {"Content-Disposition": f'{disposition}; filename="{image.filename}"'}

    return FileResponse(
        path=image.filepath,
        media_type=mime_type,
        filename=image.filename,
        headers=headers,
    )
