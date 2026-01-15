from bioscopeai_core.app.crud.base import BaseCRUD
from bioscopeai_core.app.models import User


class UsersCRUD(BaseCRUD[User]):
    """CRUD operations for User model."""

    model = User

    # async def get_by_username(self, username: str) -> User | None:
    #     """Get a user by their username."""
    #     user: User | None = await self.model.get_or_none(username=username)
    #     return user

    # async def create_user(self, user_in: UserCreate) -> User:
    #     """Create a new user with hashed password."""
    #     hashed_password = get_password_hash(user_in.password)
    #     obj: User = await self.model.create(
    #         **user_in.model_dump(exclude={"password"}),
    #         hashed_password=hashed_password,
    #     )
    #     return obj

    # async def update_user(self, user_id: UUID, user_in: UserUpdate) -> User | None:
    #     """Update an existing user's information."""
    #     user: User | None = await self.model.get_or_none(id=user_id)
    #     if not user:
    #         return None

    #     update_data = user_in.model_dump(exclude_unset=True)
    #     if "password" in update_data:
    #         hashed_password = get_password_hash(update_data.pop("password"))
    #         update_data["hashed_password"] = hashed_password

    #     for field, value in update_data.items():
    #         setattr(user, field, value)

    #     await user.save()
    #     await user.refresh_from_db()
    #     return user


def get_users_crud() -> UsersCRUD:
    """Get an instance of UsersCRUD."""
    return UsersCRUD()
