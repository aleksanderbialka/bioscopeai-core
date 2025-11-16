from typing import Annotated

from fastapi import APIRouter, Depends, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas import UserOut


users_router = APIRouter()


@users_router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_current_user(
    user: Annotated[User, Depends(require_role(UserRole.VIEWER.value))],
) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
    )
