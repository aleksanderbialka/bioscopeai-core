from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import fields, models


if TYPE_CHECKING:
    from bioscopeai_core.app.models.classification import Classification
    from bioscopeai_core.app.models.image import Image


class Dataset(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    owner = fields.ForeignKeyField("models.User", related_name="datasets")
    created_at = fields.DatetimeField(auto_now_add=True)

    images: fields.ReverseRelation[Image]
    classifications: fields.ReverseRelation[Classification]
