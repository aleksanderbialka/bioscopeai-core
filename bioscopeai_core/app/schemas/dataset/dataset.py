from datetime import datetime

from pydantic import BaseModel


class DatasetBase(BaseModel):
    """Base schema for dataset."""

    name: str
    description: str | None = None


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""


class DatasetUpdate(BaseModel):
    """Schema for partial update of a dataset."""

    name: str | None = None
    description: str | None = None


class DatasetMinimalOut(BaseModel):
    """Minimal info (e.g. in dropdowns, after creation)."""

    id: str
    name: str


class DatasetOut(DatasetBase):
    """Full dataset representation."""

    id: str
    owner_username: str
    created_at: datetime

    class Config:
        from_attributes = True
