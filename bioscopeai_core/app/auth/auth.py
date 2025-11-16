import hashlib
import secrets
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status
from jose import jwt

from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.models import RefreshToken, User


ALGORITHM = "RS256"


def create_access_token(sub: str, role: str) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.auth.ACCESS_TOKEN_TTL_MINUTES)
    return jwt.encode(  # type: ignore[no-any-return]
        {"sub": sub, "roles": role, "exp": exp, "iat": datetime.now(UTC)},
        settings.auth.PRIVATE_KEY.get_secret_value(),
        algorithm=ALGORITHM,
    )


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def obtain_token_pair(user: User) -> tuple[str, str]:
    """
    Generates and stores a new refresh token, returning a pair of access and
    refresh tokens.
    """
    access = create_access_token(str(user.id), user.role.value)
    raw_refresh = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    expires = datetime.now(UTC) + timedelta(
        minutes=settings.auth.REFRESH_TOKEN_TTL_MINUTES
    )
    await RefreshToken.create(user=user, token_hash=token_hash, exp=expires)
    return access, raw_refresh


async def rotate_refresh_token(old_raw: str) -> tuple[str, str]:
    """Rotate (revoke and issue new) refresh token."""
    hashed = hash_refresh_token(old_raw)
    obj = await RefreshToken.get_or_none(token_hash=hashed).prefetch_related("user")

    if not obj or obj.revoked or obj.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # revoke old
    obj.revoked = True
    await obj.save(update_fields=["revoked"])

    # issue new pair
    access, new_refresh = await obtain_token_pair(obj.user)
    return access, new_refresh


async def revoke_refresh(refresh_token: str) -> None:
    hashed = hash_refresh_token(refresh_token)
    await RefreshToken.filter(token_hash=hashed).update(revoked=True)
