from tortoise import fields, models


class Device(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255)
    hostname = fields.CharField(max_length=255, unique=True)
    location = fields.CharField(max_length=255, null=True)
    firmware_version = fields.CharField(max_length=50, null=True)
    is_online = fields.BooleanField(default=False)
    last_seen = fields.DatetimeField(null=True)
    registered_at = fields.DatetimeField(auto_now_add=True)
