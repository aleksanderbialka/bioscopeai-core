from datetime import datetime, UTC
from enum import StrEnum

from passlib.context import CryptContext
from tortoise import fields
from tortoise.models import Model


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserRole(StrEnum):
    """User roles in the system with hierarchy
    ADMIN > RESEARCHER > ANALYST > VIEWER
    """

    ADMIN = "admin"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    VIEWER = "viewer"

    # Define role hierarchy
    @property
    def level(self) -> int:
        levels: dict[UserRole, int] = {
            UserRole.ADMIN: 4,
            UserRole.RESEARCHER: 3,
            UserRole.ANALYST: 2,
            UserRole.VIEWER: 1,
        }
        return levels[self]

    def has_at_least(self, required: "UserRole") -> bool:
        return self.level >= required.level


class UserStatus(StrEnum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Model):
    """User model for authentication and authorization."""

    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    username = fields.CharField(max_length=50, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    role: UserRole = fields.CharEnumField(UserRole, default=UserRole.VIEWER)
    status: UserStatus = fields.CharEnumField(UserStatus, default=UserStatus.PENDING)
    institution = fields.CharField(max_length=50, null=True)
    department = fields.CharField(max_length=50, null=True)
    phone = fields.CharField(max_length=20, null=True)
    is_verified = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_login = fields.DatetimeField(null=True)
    password_reset_token = fields.CharField(max_length=255, null=True)
    password_reset_expires = fields.DatetimeField(null=True)
    email_verification_token = fields.CharField(max_length=255, null=True)
    email_verified_at = fields.DatetimeField(null=True)

    class Meta:
        table: str = "users"
        ordering: list[str] = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_active(self) -> bool:
        """User is active only when status is ACTIVE."""
        return self.status == UserStatus.ACTIVE

    @property
    def can_analyze(self) -> bool:
        """Check if user can perform analysis."""
        return self.role in {UserRole.ADMIN, UserRole.RESEARCHER, UserRole.ANALYST}

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @classmethod
    async def create_user(
        cls, email: str, username: str, first_name: str, last_name: str, password: str
    ) -> "User":
        user = cls(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            status=UserStatus.ACTIVE,
        )
        await user.set_password(password)
        await user.save()
        return user

    def has_role(self, required: UserRole) -> bool:
        """Check if user has the required role or higher."""
        return self.role.has_at_least(required)

    async def set_password(self, password: str) -> None:
        """Set hashed password."""
        self.password_hash = pwd_context.hash(password)

    async def verify_password(self, password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(secret=password, hash=self.password_hash)  # type: ignore[no-any-return]

    async def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.now(tz=UTC)
        await self.save(update_fields=["last_login"])

    def is_password_reset_token_valid(self) -> bool:
        """Check if password reset token is valid."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.now(tz=UTC) < self.password_reset_expires  # type: ignore[no-any-return]
