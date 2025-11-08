from typing import Annotated

from fastapi import APIRouter, Depends

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.models import User, UserRole


users_router = APIRouter()


@users_router.get("/me")
async def get_current_user(
    user: Annotated[User, Depends(require_role(UserRole.VIEWER.value))],
) -> dict[str, str]:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
    }
