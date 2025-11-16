from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageBase(BaseModel):
    filename: str | None = None
    analyzed: bool = False


class ImageCreate(ImageBase):
    dataset_id: UUID
    device_id: UUID | None = None


class ImageUpdate(BaseModel):
    filename: str | None = None
    analyzed: bool | None = None
    device_id: UUID | None = None


class ImageMinimalOut(BaseModel):
    id: UUID
    filename: str
    analyzed: bool


class ImageOut(ImageBase):
    id: UUID
    dataset_id: UUID
    uploaded_by_id: UUID
    device_id: UUID | None = None
    filepath: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
