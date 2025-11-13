from datetime import datetime, UTC
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.device import DeviceCRUD, get_device_crud
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.models.device.device import Device
from bioscopeai_core.app.schemas.device import (
    DeviceCreate,
    DeviceMinimalOut,
    DeviceOut,
    DeviceStatusUpdate,
    DeviceUpdate,
)
from bioscopeai_core.app.serializers.device import (
    DeviceSerializer,
    get_device_serializer,
)


device_router = APIRouter()


@device_router.get("/", response_model=list[DeviceOut], status_code=status.HTTP_200_OK)
async def list_devices(
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    device_serializer: Annotated[DeviceSerializer, Depends(get_device_serializer)],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
    is_online: Annotated[
        bool | None, Query(description="Filter devices by online status")
    ] = None,
    location: Annotated[
        str | None, Query(description="Filter devices by location")
    ] = None,
) -> list[DeviceOut]:
    devices = await device_crud.get_filtered_devices(
        is_online=is_online, location=location
    )
    return device_serializer.device_to_out_list(devices)


@device_router.get(
    "/{device_id}",
    response_model=DeviceOut,
    status_code=status.HTTP_200_OK,
)
async def get_device(
    device_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ANALYST.value))],
    device_serializer: Annotated[DeviceSerializer, Depends(get_device_serializer)],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
) -> DeviceOut:
    device = await device_crud.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )
    return device_serializer.device_to_out(device)


@device_router.post(
    "/", response_model=DeviceMinimalOut, status_code=status.HTTP_201_CREATED
)
async def register_device(
    device_in: DeviceCreate,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    device_serializer: Annotated[DeviceSerializer, Depends(get_device_serializer)],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
) -> DeviceMinimalOut:
    device: Device = await device_crud.create_device(device_in)
    return device_serializer.device_to_out_minimal(device)


@device_router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_device(
    device_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
) -> None:
    deleted = await device_crud.delete_by_id(device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")


@device_router.patch(
    "/{device_id}",
    response_model=DeviceOut,
    status_code=status.HTTP_200_OK,
)
async def update_device(
    device_id: UUID,
    device_in: DeviceUpdate,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    device_serializer: Annotated[DeviceSerializer, Depends(get_device_serializer)],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
) -> DeviceOut:
    updated = await device_crud.update_device(device_id, device_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )
    return device_serializer.device_to_out(updated)


@device_router.patch(
    "/{device_id}/status",
    response_model=DeviceOut,
    status_code=status.HTTP_200_OK,
)
async def update_device_status(
    device_id: UUID,
    status_in: DeviceStatusUpdate,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    device_crud: Annotated[DeviceCRUD, Depends(get_device_crud)],
    device_serializer: Annotated[DeviceSerializer, Depends(get_device_serializer)],
) -> DeviceOut:
    device = await device_crud.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )
    device.is_online = status_in.is_online
    if status_in.is_online:
        device.last_seen = datetime.now(UTC)
    await device.save()
    return device_serializer.device_to_out(device)
