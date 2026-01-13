"""Integration tests for authentication API endpoints."""

import pytest
from httpx import AsyncClient

from bioscopeai_core.app.models import User
from bioscopeai_core.app.models.users.user import UserRole

TEST_PASSWORD = "SecurePass123!"


@pytest.fixture
async def test_user_with_password() -> User:
    user = await User.create_user(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        password=TEST_PASSWORD,
    )
    user.role = UserRole.RESEARCHER
    await user.save()
    return user


@pytest.fixture
def valid_registration_data() -> dict[str, str]:
    return {
        "email": "newuser@test.example.com",
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "password": TEST_PASSWORD,
    }


@pytest.fixture
def valid_login_data() -> dict[str, str]:
    return {
        "email": "test@example.com",
        "password": TEST_PASSWORD,
    }


class TestRegisterEndpoint:
    async def test_successful_registration(
        self, api_client: AsyncClient, valid_registration_data: dict[str, str]
    ):
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == valid_registration_data["email"]

        user = await User.get_or_none(email=valid_registration_data["email"])
        assert user is not None
        assert user.username == valid_registration_data["username"]
        assert user.role == UserRole.VIEWER

    async def test_duplicate_email_rejected(
        self, api_client: AsyncClient, test_user_with_password: User, valid_registration_data: dict
    ):
        valid_registration_data["email"] = test_user_with_password.email
        valid_registration_data["username"] = "different_username"
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )
        assert response.status_code == 400
        assert "Email already used" in response.json()["detail"]

    async def test_duplicate_username_rejected(
        self, api_client: AsyncClient, test_user_with_password: User, valid_registration_data: dict
    ):
        valid_registration_data["username"] = test_user_with_password.username
        valid_registration_data["email"] = "unique@test.example.com"
        response = await api_client.post(
            "/api/auth/register", json=valid_registration_data
        )
        assert response.status_code == 400
        assert "Username already used" in response.json()["detail"]

    @pytest.mark.parametrize(
        "missing_field",
        ["email", "username", "first_name", "last_name", "password"],
    )
    async def test_missing_required_field_rejected(
        self,
        api_client: AsyncClient,
        valid_registration_data: dict[str, str],
        missing_field: str,
    ):
        del valid_registration_data[missing_field]
        response = await api_client.post("/api/auth/register", json=valid_registration_data)
        assert response.status_code == 422


class TestLoginEndpoint:
    async def test_successful_login_returns_tokens(
        self, api_client: AsyncClient, test_user_with_password: User
    ):
        login_data = {"email": test_user_with_password.email, "password": TEST_PASSWORD}
        response = await api_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" in response.cookies

    async def test_login_with_wrong_password_unauthorized(
        self, api_client: AsyncClient, test_user_with_password: User
    ):
        login_data = {"email": test_user_with_password.email, "password": "WrongPassword"}
        response = await api_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_with_nonexistent_user_unauthorized(
        self, api_client: AsyncClient
    ):
        login_data = {"email": "nonexistent@test.example.com", "password": TEST_PASSWORD}
        response = await api_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_login_updates_last_login_timestamp(
        self, api_client: AsyncClient, test_user_with_password: User
    ):
        assert test_user_with_password.last_login is None
        login_data = {"email": test_user_with_password.email, "password": TEST_PASSWORD}

        await api_client.post("/api/auth/login", json=login_data)
        await test_user_with_password.refresh_from_db()

        assert test_user_with_password.last_login is not None


class TestRefreshTokenEndpoint:
    async def test_successful_token_refresh(
        self, api_client: AsyncClient, test_user_with_password: User
    ):
        login_data = {"email": test_user_with_password.email, "password": TEST_PASSWORD}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.cookies.get("refresh_token")

        api_client.cookies.set("refresh_token", refresh_token)
        response = await api_client.post("/api/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "refresh_token" in response.cookies
        assert response.cookies.get("refresh_token") != refresh_token

    async def test_refresh_without_token_unauthorized(self, api_client: AsyncClient):
        response = await api_client.post("/api/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_with_invalid_token_unauthorized(
        self, api_client: AsyncClient
    ):
        api_client.cookies.set("refresh_token", "invalid_token_xyz")
        response = await api_client.post("/api/auth/refresh")
        assert response.status_code == 401


class TestLogoutEndpoint:
    async def test_successful_logout_revokes_token(
        self, api_client: AsyncClient, test_user_with_password: User
    ):
        login_data = {"email": test_user_with_password.email, "password": TEST_PASSWORD}
        login_response = await api_client.post("/api/auth/login", json=login_data)
        refresh_token = login_response.cookies.get("refresh_token")

        api_client.cookies.set("refresh_token", refresh_token)
        response = await api_client.post("/api/auth/logout")
        assert response.status_code == 204

        response = await api_client.post("/api/auth/refresh")
        assert response.status_code == 401

    async def test_logout_without_token_returns_unauthorized(
        self, api_client: AsyncClient
    ):
        response = await api_client.post("/api/auth/logout")
        assert response.status_code == 401
