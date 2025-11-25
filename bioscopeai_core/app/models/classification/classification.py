from enum import StrEnum

from tortoise import fields, models


class ClassificationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Classification(models.Model):
    id = fields.UUIDField(pk=True)
    image = fields.ForeignKeyField(
        "models.Image", related_name="classifications", null=True
    )
    dataset = fields.ForeignKeyField(
        "models.Dataset", related_name="classifications", null=True
    )
    model_name = fields.CharField(max_length=100, null=True)
    status = fields.CharEnumField(
        ClassificationStatus, default=ClassificationStatus.PENDING
    )
    created_by = fields.ForeignKeyField("models.User", related_name="classifications")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
