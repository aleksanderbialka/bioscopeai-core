from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from bioscopeai_core.app.auth.service_user import ServiceUser
from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.models import User, UserRole

from .auth import ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login-swagger")


async def get_user_from_jwt(
    token: str = Depends(dependency=oauth2_scheme),
) -> User | ServiceUser:
    """Decode JWT token and return the associated user or service pseudo-user."""
    try:
        payload = jwt.decode(token, settings.auth.PUBLIC_KEY, algorithms=ALGORITHM)
        user_id = payload.get("sub")
        role = payload.get("roles")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Handle service tokens
        if role == UserRole.SERVICE.value:
            return ServiceUser(service_name=user_id)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from e

    # Regular user token
    user: User | None = await User.get_or_none(id=user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User disabled"
        )
    return user


async def verify_login(email: str, password: str) -> User:
    """Verify user credentials and return the user if valid."""
    user: User | None = await User.get_or_none(email=email)
    if not user or not await user.verify_password(password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return user


def require_role(required_role: str) -> Callable[..., User | ServiceUser]:
    """Dependency to verify that the user has the required role.
    Returns the user if the role requirement is met.
    Raises 403 Forbidden otherwise.
    """

    def dependency(
        user: Annotated[User | ServiceUser, Depends(get_user_from_jwt)],
    ) -> User | ServiceUser:
        if not user.has_role(UserRole(required_role)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency
