from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from bioscopeai_core.app.models import UserRole


class UserOut(BaseModel):
    model_config: ConfigDict = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role: UserRole


@field_serializer("role")
def serialize_role(self, role: UserRole) -> str:  # type: ignore[no-untyped-def]
    return role.value if hasattr(role, "value") else str(role)
