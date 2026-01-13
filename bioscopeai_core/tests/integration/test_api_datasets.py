"""Integration tests for dataset API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import UUID

from bioscopeai_core.app.models import User, Dataset
from bioscopeai_core.app.models.users.user import UserRole
from bioscopeai_core.tests.conftest import (
    TEST_PASSWORD,
    create_analyst_user,
    get_auth_token,
)


@pytest.fixture
async def analyst_user() -> User:
    return await create_analyst_user("analyst@test.example.com")


@pytest.fixture
async def analyst_headers(api_client: AsyncClient, analyst_user: User) -> dict:
    token = await get_auth_token(api_client, analyst_user.email, TEST_PASSWORD)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_dataset(analyst_user: User) -> Dataset:
    return await Dataset.create(
        name="Test Dataset",
        description="Test dataset for integration tests",
        owner=analyst_user,
    )


class TestListDatasets:
    async def test_returns_user_datasets(
        self, api_client: AsyncClient, analyst_headers: dict, test_dataset: Dataset
    ):
        response = await api_client.get("/api/datasets/", headers=analyst_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_dataset.id)
        assert data[0]["name"] == test_dataset.name

    async def test_returns_empty_list_for_user_without_datasets(
        self, api_client: AsyncClient
    ):
        new_analyst = await create_analyst_user("another@test.example.com")
        token = await get_auth_token(api_client, new_analyst.email, TEST_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}

        response = await api_client.get("/api/datasets/", headers=headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_requires_analyst_role(self, api_client: AsyncClient):
        viewer = await User.create_user(
            email="viewer@test.example.com",
            username="viewer",
            first_name="Test",
            last_name="Viewer",
            password="ViewerPass123!",
        )
        token = await get_auth_token(api_client, viewer.email, "ViewerPass123!")
        headers = {"Authorization": f"Bearer {token}"}

        response = await api_client.get("/api/datasets/", headers=headers)
        assert response.status_code == 403


class TestCreateDataset:
    async def test_creates_new_dataset(
        self, api_client: AsyncClient, analyst_headers: dict, analyst_user: User
    ):
        dataset_data = {
            "name": "New Dataset",
            "description": "Created via API",
        }

        response = await api_client.post(
            "/api/datasets/", json=dataset_data, headers=analyst_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert UUID(data["id"])
        assert data["name"] == dataset_data["name"]

        dataset = await Dataset.get_or_none(id=data["id"])
        assert dataset is not None
        assert dataset.owner_id == analyst_user.id

    async def test_requires_name(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        response = await api_client.post(
            "/api/datasets/", json={"description": "No name"}, headers=analyst_headers
        )
        assert response.status_code == 422

    async def test_requires_authentication(self, api_client: AsyncClient):
        response = await api_client.post(
            "/api/datasets/", json={"name": "Test", "description": "Test"}
        )
        assert response.status_code == 401


class TestGetDataset:
    async def test_returns_dataset_details(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_dataset: Dataset,
    ):
        response = await api_client.get(
            f"/api/datasets/{test_dataset.id}", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_dataset.id)
        assert data["name"] == test_dataset.name
        assert data["description"] == test_dataset.description

    async def test_returns_404_for_nonexistent_dataset(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.get(f"/api/datasets/{fake_id}", headers=analyst_headers)
        assert response.status_code == 404

    async def test_returns_404_for_other_user_dataset(
        self, api_client: AsyncClient, test_dataset: Dataset
    ):
        other_analyst = await create_analyst_user("other@test.example.com")
        token = await get_auth_token(api_client, other_analyst.email, TEST_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}

        response = await api_client.get(
            f"/api/datasets/{test_dataset.id}", headers=headers
        )
        assert response.status_code == 404


class TestUpdateDataset:
    async def test_updates_dataset_fields(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_dataset: Dataset,
    ):
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
        }

        response = await api_client.patch(
            f"/api/datasets/{test_dataset.id}",
            json=update_data,
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

        await test_dataset.refresh_from_db()
        assert test_dataset.name == update_data["name"]

    async def test_returns_404_for_nonexistent_dataset(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.patch(
            f"/api/datasets/{fake_id}",
            json={"name": "Updated"},
            headers=analyst_headers,
        )
        assert response.status_code == 404


class TestDeleteDataset:
    async def test_deletes_dataset(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_dataset: Dataset,
    ):
        dataset_id = test_dataset.id

        response = await api_client.delete(
            f"/api/datasets/{dataset_id}", headers=analyst_headers
        )

        assert response.status_code == 204
        dataset = await Dataset.get_or_none(id=dataset_id)
        assert dataset is None

    async def test_returns_404_for_nonexistent_dataset(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.delete(
            f"/api/datasets/{fake_id}", headers=analyst_headers
        )
        assert response.status_code == 404
