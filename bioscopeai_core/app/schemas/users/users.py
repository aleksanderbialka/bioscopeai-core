from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from bioscopeai_core.app.models import UserRole, UserStatus


class UserOut(BaseModel):
    """Schema for user output."""

    model_config: ConfigDict = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    institution: str | None = None
    department: str | None = None
    phone: str | None = None


@field_serializer("role")
def serialize_role(self, role: UserRole) -> str:  # type: ignore[no-untyped-def]
    return role.value if hasattr(role, "value") else str(role)


@field_serializer("status")
def serialize_status(self, status: UserStatus) -> str:  # type: ignore[no-untyped-def]
    return status.value if hasattr(status, "value") else str(status)


class UserUpdateBase(BaseModel):
    """Base schema with common fields for user updates."""

    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    institution: str | None = Field(None, max_length=50)
    department: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=20)


class UserUpdateMe(UserUpdateBase):
    """Schema for users to update their own profile.
    Users can only update safe fields. Role and status changes require admin privileges.
    """

    password: str | None = Field(
        None, min_length=8, max_length=100, description="New password"
    )


class UserUpdateAdmin(UserUpdateBase):
    """Schema for admins to update any user profile, including role and status.
    Password changes are excluded - users can only change their own password.
    """

    role: UserRole | None = None
    status: UserStatus | None = None
