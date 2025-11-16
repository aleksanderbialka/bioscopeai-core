from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ClassificationResultCreate(BaseModel):
    image_id: UUID
    classification_id: UUID | None = None
    label: str
    confidence: float
    model_name: str | None = None


class ClassificationResultOut(BaseModel):
    id: UUID
    image_id: UUID
    classification_id: UUID | None
    label: str
    confidence: float
    model_name: str | None
    created_at: datetime
