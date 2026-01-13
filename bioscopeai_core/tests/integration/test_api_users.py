"""Integration tests for users API endpoints."""

import pytest
from httpx import AsyncClient

from bioscopeai_core.app.models import User
from bioscopeai_core.tests.conftest import get_auth_token


@pytest.fixture
async def researcher_with_password() -> User:
    return await User.create_user(
        email="researcher@test.example.com",
        username="researcher",
        first_name="John",
        last_name="Researcher",
        password="ResearchPass123!",
    )


class TestGetCurrentUser:
    async def test_returns_authenticated_user_info(
        self, api_client: AsyncClient, researcher_with_password: User
    ):
        token = await get_auth_token(
            api_client, researcher_with_password.email, "ResearchPass123!"
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = await api_client.get("/api/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(researcher_with_password.id)
        assert data["email"] == researcher_with_password.email
        assert data["username"] == researcher_with_password.username
        assert data["first_name"] == researcher_with_password.first_name
        assert data["last_name"] == researcher_with_password.last_name
        assert data["role"] == researcher_with_password.role.value

    async def test_unauthorized_without_token(self, api_client: AsyncClient):
        response = await api_client.get("/api/users/me")
        assert response.status_code == 401

    async def test_unauthorized_with_invalid_token(self, api_client: AsyncClient):
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = await api_client.get("/api/users/me", headers=headers)
        assert response.status_code == 401
