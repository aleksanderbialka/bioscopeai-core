from tortoise import fields, models


class Image(models.Model):
    id = fields.UUIDField(pk=True)
    filename = fields.CharField(max_length=255)
    filepath = fields.CharField(max_length=512)
    dataset = fields.ForeignKeyField("models.Dataset", related_name="images")
    uploaded_by = fields.ForeignKeyField("models.User", related_name="uploaded_images")
    device = fields.ForeignKeyField("models.Device", related_name="images", null=True)
    uploaded_at = fields.DatetimeField(auto_now_add=True)
    analyzed = fields.BooleanField(default=False)
