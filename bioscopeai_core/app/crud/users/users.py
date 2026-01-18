from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger

from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models import User, UserRole
from bioscopeai_core.app.schemas.users.users import UserUpdateAdmin, UserUpdateMe


class UsersCRUD(BaseCRUD[User]):
    """CRUD operations for User model."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by their email address."""
        user: User | None = await self.model.get_or_none(email=email)
        return user

    async def update_user(
        self,
        user_id: UUID,
        update_data: UserUpdateMe | UserUpdateAdmin,
        actor: User,
    ) -> User:
        """Update user with proper authorization checks."""
        target_user = await self.get_by_id(user_id)
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return target_user

        # Check permissions
        is_self_update = user_id == actor.id
        is_admin = actor.role == UserRole.ADMIN

        if not is_self_update and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update other users",
            )

        privileged_fields = {"role", "status"}
        if not is_admin and any(field in update_dict for field in privileged_fields):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update role and status",
            )

        # Password can only be changed by self
        if "password" in update_dict and not is_self_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password",
            )

        # Validate email uniqueness
        if "email" in update_dict and update_dict["email"] != target_user.email:
            existing_user = await self.get_by_email(update_dict["email"])
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        if "password" in update_dict:
            password = update_dict.pop("password")
            await target_user.set_password(password)

        for field, value in update_dict.items():
            setattr(target_user, field, value)

        await target_user.save()
        logger.info(
            f"User {actor.id} ({actor.username}) updated user {user_id} "
            f"with fields: {list(update_dict.keys())}"
        )
        return target_user


def get_users_crud() -> UsersCRUD:
    """Get an instance of UsersCRUD."""
    return UsersCRUD()
