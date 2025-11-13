from typing import cast
from uuid import UUID

from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models.device import Device
from bioscopeai_core.app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceCRUD(BaseCRUD[Device]):
    model = Device

    async def get_filtered_devices(
        self, is_online: bool | None = None, location: str | None = None
    ) -> list[Device]:
        query = self.model.all()
        if is_online:
            query = query.filter(is_online=is_online)
        if location:
            query = query.filter(location=location)
        return cast("list[Device]", await query)

    async def create_device(self, device_in: DeviceCreate) -> Device:
        return cast("Device", await self.model.create(**device_in.model_dump()))

    async def update_device(
        self, device_id: UUID, device_in: DeviceUpdate
    ) -> Device | None:
        device: Device | None = await self.model.get_or_none(id=device_id)
        if not device:
            return None

        # Update only provided fields
        update_data = device_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        await device.save()
        await device.refresh_from_db()
        return device


def get_device_crud() -> DeviceCRUD:
    return DeviceCRUD()
