"""Pytest configuration and shared fixtures."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC

import pytest
from pydantic import SecretStr

from bioscopeai_core.app.models import RefreshToken, User
from bioscopeai_core.app.models.users.user import UserRole, UserStatus


TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC9kN5XP5E0nPG+
PfimCvRQdbzqwEWpGwG0s7+COOnyYNkINsPDMLhKljDfgla8hjKQkWDipQtWYAEw
ZL2O664Fhlqhubv7SC+YE2fRKRkE5RipX4CLEkdjHUqnkav76iF/mHTHATyaZ/uX
Wy4DC80bq+4AYNUpmHFnwNgXc+ieQwBCt8FyCUvVN71Uxdv7Oz5vxarjheeinKhv
kLy0Yo+0cK8FmKj78TR5OUMezUEY22tozLu7LPcDkQU/VQklbKJOS+PcaoNwTi1g
cfJsgYozYB+TnLdISVyJ4mtOxP4lMUw+KKtFLKi5fJF9KBuI8v++IuXQgMpk+pNX
j7FLHHrDAgMBAAECggEAXVu/ZJC13od8twimMIAsmoOhqqtOo13dlTUBGA0XinsP
5++wsayI1pLpNupl9SrSNEikwnot/zgA3eh/QqfnaGkmsYdbgQGoDulfs67d139M
if2yvMsfxTxjy+r+HG7OWJyoxmlhg1m6mmwZWP6y4PHnoOAPmxCsqUBcLBC1e1sD
Aj9bzB+jxohPe5XqNFRWVzj9T5+0lxrMZMrsMTy9EmutxxINgFJ/LVLyeEDG47oh
StjQ6uBSjydQZFRWV5VZd4lzLTgV/k4r7tDMTqehs2yX9vgRo6WDbaGJEtpS4j2k
Vnq3r7pjlWa9LBUSdEi59QBiwpjL4WE3HgTr2+kcgQKBgQDewELweAWJ/yK+or/k
Lzsh6sZLPWFI60HHBSAtJLSKNpooyuQmgOlGS/FJ6BHsKLcsror8i+0FMEyiFI5m
9WMouvW/069KwWWS5sxQkVkMyF/4lqHDeoQLQYMo7YxwDQi1H8nyJCGSR5+xfPmt
+zmg6TYqFOwYpNTPZ6iBDnM8UwKBgQDZ3IpXoJ1ABsgCwdf7dZbit7ObWmd3OfIP
hHXyStugKgrvSQPaT+IVtZer92lz7kL6003OANMEQy7RKktS31PdaU7CO3e2xswY
a8bbUR4Ec+3h/KGK6zAVhFvoFV4zUh5SflmI2pgmBipEVCzKLw8kB3I9X+1JUmW4
xogW8cd50QKBgGVXIx0z/ZEiujPw50xxEH4FyeFBM5lxLqPU+SaQpHKdFNWqONIr
o/WPZ18wbbb7bxqs7h6nqlXJ+5NhtsewrERDirqTHBTul7+VsS6WceUW5FK8dSvx
+VEFpR5htJrl0yhUJhQ7y+o5G7YsHYvB2B4U+8d5bVBo7UjO6CKO6G5xAoGBAIix
d5vDiubBWn1gYsPD5AgcevTepEyKbvaNhfOgRG0Z9AJvLZusw44bgi7D7cZvmFcI
fajjm4LxJE7Y2qoEtfoWOPRlm5dy5FvuQ7cYDl1836ULfdBMAL9/bKsRvSk2PRBF
dqgHf69b7ukwZ2n0XOueQG+B4MBAktJ8vqamzSIBAoGBAIIWDMm5IVsKoLLwdyQi
mb29Q5RVOXm1JYOesOafO+SlDGQT70xId1MjKnLOiVE1eZlXCl2GdCApnZYxRqZa
Nzt08lzIi7WzgKDrAnpOwtu+IsQnj0/JN7zkPed1hfuYmziwHSn2EEnNPsdaRbKw
BxzL4tZU+GpG4VLazFXqjBVq
-----END PRIVATE KEY-----"""

TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvZDeVz+RNJzxvj34pgr0
UHW86sBFqRsBtLO/gjjp8mDZCDbDwzC4SpYw34JWvIYykJFg4qULVmABMGS9juuu
BYZaobm7+0gvmBNn0SkZBOUYqV+AixJHYx1Kp5Gr++ohf5h0xwE8mmf7l1suAwvN
G6vuAGDVKZhxZ8DYF3PonkMAQrfBcglL1Te9VMXb+zs+b8Wq44Xnopyob5C8tGKP
tHCvBZio+/E0eTlDHs1BGNtraMy7uyz3A5EFP1UJJWyiTkvj3GqDcE4tYHHybIGK
M2Afk5y3SElcieJrTsT+JTFMPiirRSyouXyRfSgbiPL/viLl0IDKZPqTV4+xSxx6
wwIDAQAB
-----END PUBLIC KEY-----"""


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[None]:
    """Initialize isolated in-memory SQLite database for each test."""
    from tortoise import Tortoise

    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["bioscopeai_core.app.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@dataclass
class MockAuthSettings:
    """Mock authentication settings."""

    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_MINUTES: int = 10080  # 7 days
    PRIVATE_KEY: SecretStr = SecretStr(TEST_PRIVATE_KEY)
    PUBLIC_KEY: str = TEST_PUBLIC_KEY


@pytest.fixture
def mock_auth_settings() -> MockAuthSettings:
    """Mock authentication settings fixture."""
    return MockAuthSettings()


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, mock_auth_settings: MockAuthSettings):
    """Auto-patch settings for all tests."""
    monkeypatch.setattr(
        "bioscopeai_core.app.auth.auth.settings.auth", mock_auth_settings
    )
    return mock_auth_settings


class UserFactory:
    """Factory for creating test users with various configurations."""

    _counter = 0

    @classmethod
    async def create(
        cls,
        email: str | None = None,
        role: UserRole = UserRole.RESEARCHER,
        status: UserStatus = UserStatus.ACTIVE,
        **kwargs,
    ) -> User:
        """Create test user with auto-generated email if not provided."""
        cls._counter += 1
        if email is None:
            email = f"user{cls._counter}@test.example.com"

        defaults = {
            "username": f"user{cls._counter}",
            "first_name": f"Test{cls._counter}",
            "last_name": "User",
            "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$test_hash",
            "role": role,
            "status": status,
        }
        defaults.update(kwargs)

        return await User.create(email=email, **defaults)


@pytest.fixture
def user_factory() -> type[UserFactory]:
    """User factory fixture."""
    return UserFactory


@pytest.fixture
async def test_user(db, user_factory: type[UserFactory]) -> User:
    """Standard test user with RESEARCHER role."""
    return await user_factory.create(
        email="test@example.com",
        role=UserRole.RESEARCHER,
    )


@pytest.fixture
async def admin_user(db, user_factory: type[UserFactory]) -> User:
    """Test admin user with elevated privileges."""
    return await user_factory.create(
        email="admin@example.com",
        first_name="Admin",
        role=UserRole.ADMIN,
    )


@pytest.fixture
async def viewer_user(db, user_factory: type[UserFactory]) -> User:
    """Test user with minimal VIEWER permissions."""
    return await user_factory.create(
        email="viewer@example.com",
        role=UserRole.VIEWER,
    )


@pytest.fixture
async def inactive_user(db, user_factory: type[UserFactory]) -> User:
    """Test user with INACTIVE status."""
    return await user_factory.create(
        email="inactive@example.com",
        status=UserStatus.INACTIVE,
    )


class RefreshTokenFactory:
    """Factory for creating refresh tokens with various states."""

    @staticmethod
    async def create(
        user: User,
        token_hash: str,
        revoked: bool = False,
        exp_delta: timedelta = timedelta(days=7),
    ) -> RefreshToken:
        """Create refresh token with specified parameters."""
        return await RefreshToken.create(
            user=user,
            token_hash=token_hash,
            exp=datetime.now(UTC) + exp_delta,
            revoked=revoked,
        )


@pytest.fixture
def token_factory() -> type[RefreshTokenFactory]:
    """Refresh token factory fixture."""
    return RefreshTokenFactory


@pytest.fixture
async def valid_refresh_token(
    test_user: User, token_factory: type[RefreshTokenFactory]
) -> tuple[RefreshToken, str]:
    """Valid refresh token with raw value tuple."""
    raw_token = "valid_test_token_12345"
    from bioscopeai_core.app.auth.auth import hash_refresh_token

    token_hash = hash_refresh_token(raw_token)
    token = await token_factory.create(user=test_user, token_hash=token_hash)

    return token, raw_token


@pytest.fixture
async def expired_refresh_token(
    test_user: User, token_factory: type[RefreshTokenFactory]
) -> tuple[RefreshToken, str]:
    """Expired refresh token with raw value tuple."""
    raw_token = "expired_test_token_67890"
    from bioscopeai_core.app.auth.auth import hash_refresh_token

    token_hash = hash_refresh_token(raw_token)
    token = await token_factory.create(
        user=test_user,
        token_hash=token_hash,
        exp_delta=timedelta(days=-1),
    )

    return token, raw_token


@pytest.fixture
async def revoked_refresh_token(
    test_user: User, token_factory: type[RefreshTokenFactory]
) -> tuple[RefreshToken, str]:
    """Revoked refresh token with raw value tuple."""
    raw_token = "revoked_test_token_abcde"
    from bioscopeai_core.app.auth.auth import hash_refresh_token

    token_hash = hash_refresh_token(raw_token)
    token = await token_factory.create(
        user=test_user,
        token_hash=token_hash,
        revoked=True,
    )

    return token, raw_token
