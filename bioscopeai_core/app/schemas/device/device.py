from datetime import datetime

from pydantic import BaseModel


class DeviceBase(BaseModel):
    """Base schema for device."""

    name: str
    hostname: str
    location: str | None = None
    firmware_version: str | None = None


class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""


class DeviceOut(DeviceBase):
    """Full response (GET/list)"""

    id: str
    is_online: bool
    last_seen: datetime | None = None
    registered_at: datetime


class DeviceMinimalOut(BaseModel):
    """Minimal response (e.g., after creation)"""

    id: str
    name: str


class DeviceUpdate(BaseModel):
    """Schema for updating device information."""

    name: str | None = None
    hostname: str | None = None
    location: str | None = None
    firmware_version: str | None = None


class DeviceStatusUpdate(BaseModel):
    """Schema for updating device status."""

    is_online: bool
