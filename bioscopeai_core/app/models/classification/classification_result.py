from tortoise import fields, models


class ClassificationResult(models.Model):
    id = fields.UUIDField(pk=True)
    image = fields.ForeignKeyField("models.Image", related_name="results")
    classification = fields.ForeignKeyField(
        "models.Classification", related_name="results", null=True
    )
    label = fields.CharField(max_length=100)
    confidence = fields.FloatField()
    model_name = fields.CharField(max_length=100, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
