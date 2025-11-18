from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from bioscopeai_core.app.models.classification import ClassificationStatus


class ClassificationCreate(BaseModel):
    """
    Payload to start a new classification job.

    Exactly one of `dataset_id` or `image_id` should be provided.
    """

    dataset_id: UUID | None = None
    image_id: UUID | None = None
    model_name: str | None = None


class ClassificationOut(BaseModel):
    """Full representation of a classification job."""

    id: UUID
    dataset_id: UUID | None
    image_id: UUID | None
    model_name: str
    status: ClassificationStatus
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


class ClassificationMinimalOut(BaseModel):
    """Minimal view (e.g. after creation)."""

    id: UUID
    status: ClassificationStatus
