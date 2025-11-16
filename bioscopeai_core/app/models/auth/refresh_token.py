from datetime import datetime, UTC

from tortoise import fields, models


class RefreshToken(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens")
    token_hash = fields.CharField(255, unique=True)
    exp = fields.DatetimeField()
    iat = fields.DatetimeField(auto_now_add=True)
    revoked = fields.BooleanField(default=False)

    class Meta:
        table = "refresh_tokens"
        indexes = ("exp", "revoked")

    @property
    def is_expired(self) -> bool:
        return self.exp < datetime.now(UTC)  # type: ignore[no-any-return]
