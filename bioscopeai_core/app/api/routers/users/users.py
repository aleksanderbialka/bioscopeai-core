from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from bioscopeai_core.app.auth.permissions import require_role
from bioscopeai_core.app.crud.users import get_users_crud, UsersCRUD
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas import UserOut
from bioscopeai_core.app.schemas.users.users import UserUpdateAdmin, UserUpdateMe


users_router = APIRouter()


@users_router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_current_user(
    user: Annotated[User, Depends(require_role(UserRole.VIEWER.value))],
) -> UserOut:
    return UserOut.model_validate(user)


@users_router.get(
    "/users", response_model=list[UserOut], status_code=status.HTTP_200_OK
)
async def get_all_users(
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    users_crud: Annotated[UsersCRUD, Depends(get_users_crud)],
) -> list[UserOut]:
    users = await users_crud.get_all()
    return [UserOut.model_validate(user) for user in users]


@users_router.get(
    "/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK
)
async def get_user_by_id(
    user_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    users_crud: Annotated[UsersCRUD, Depends(get_users_crud)],
) -> UserOut:
    target_user = await users_crud.get_by_id(user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserOut.model_validate(target_user)


@users_router.patch(
    "/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK
)
async def update_user_by_id(
    user_id: UUID,
    user_update: UserUpdateMe | UserUpdateAdmin,
    user: Annotated[User, Depends(require_role(UserRole.VIEWER.value))],
    users_crud: Annotated[UsersCRUD, Depends(get_users_crud)],
) -> UserOut:
    """Update user profile.
    - Users can update their own profile with safe fields only
    - Admins can update any user including role and status
    """
    updated_user = await users_crud.update_user(user_id, user_update, actor=user)
    return UserOut.model_validate(updated_user)


@users_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: UUID,
    user: Annotated[User, Depends(require_role(UserRole.ADMIN.value))],
    users_crud: Annotated[UsersCRUD, Depends(get_users_crud)],
) -> None:
    await users_crud.delete_by_id(user_id)
