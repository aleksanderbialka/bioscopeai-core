"""Integration tests for image API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import UUID

from bioscopeai_core.app.models import User, Dataset, Device, Image
from bioscopeai_core.app.models.users.user import UserRole
from bioscopeai_core.tests.conftest import (
    TEST_PASSWORD,
    create_analyst_user,
    create_admin_user,
    get_auth_token,
)


@pytest.fixture
async def analyst_user() -> User:
    return await create_analyst_user("analyst@test.example.com")


@pytest.fixture
async def admin_user() -> User:
    return await create_admin_user("admin@test.example.com")


@pytest.fixture
async def analyst_headers(api_client: AsyncClient, analyst_user: User) -> dict:
    token = await get_auth_token(api_client, analyst_user.email, TEST_PASSWORD)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(api_client: AsyncClient, admin_user: User) -> dict:
    token = await get_auth_token(api_client, admin_user.email, TEST_PASSWORD)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_dataset(analyst_user: User) -> Dataset:
    return await Dataset.create(
        name="Test Dataset",
        description="Dataset for image tests",
        owner=analyst_user,
    )


@pytest.fixture
async def test_device(analyst_user: User) -> Device:
    return await Device.create(
        name="Test Device",
        hostname="test-device-001",
    )


@pytest.fixture
async def test_image(analyst_user: User, test_dataset: Dataset, test_device: Device) -> Image:
    return await Image.create(
        dataset=test_dataset,
        device=test_device,
        uploaded_by=analyst_user,
        filename="test_image.jpg",
        filepath="/tmp/test_image.jpg",
        file_size=1024,
        width=800,
        height=600,
    )


class TestListImages:
    async def test_returns_images_list(
        self, api_client: AsyncClient, analyst_headers: dict, test_image: Image
    ):
        response = await api_client.get("/api/images/", headers=analyst_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_image.id)
        assert data[0]["filename"] == test_image.filename

    async def test_filters_by_dataset_id(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        analyst_user: User,
        test_dataset: Dataset,
        test_image: Image,
    ):
        other_dataset = await Dataset.create(
            name="Other Dataset", owner=analyst_user
        )
        await Image.create(
            dataset=other_dataset,
            uploaded_by=analyst_user,
            filename="other.jpg",
            filepath="/tmp/other.jpg",
            file_size=512,
        )

        response = await api_client.get(
            f"/api/images/?dataset_id={test_dataset.id}", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(test_image.id)

    async def test_filters_by_analyzed_status(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        analyst_user: User,
        test_dataset: Dataset,
    ):
        analyzed_image = await Image.create(
            dataset=test_dataset,
            uploaded_by=analyst_user,
            filename="analyzed.jpg",
            filepath="/tmp/analyzed.jpg",
            file_size=1024,
            analyzed=True,
        )

        response = await api_client.get(
            "/api/images/?analyzed=true", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(analyzed_image.id)

    async def test_pagination_works(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        analyst_user: User,
        test_dataset: Dataset,
    ):
        for i in range(5):
            await Image.create(
                dataset=test_dataset,
                uploaded_by=analyst_user,
                filename=f"image_{i}.jpg",
                filepath=f"/tmp/image_{i}.jpg",
                file_size=1024,
            )

        response = await api_client.get(
            "/api/images/?page=1&page_size=2", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

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

        response = await api_client.get("/api/images/", headers=headers)
        assert response.status_code == 403


class TestGetImage:
    async def test_returns_image_details(
        self, api_client: AsyncClient, analyst_headers: dict, test_image: Image
    ):
        response = await api_client.get(
            f"/api/images/{test_image.id}", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_image.id)
        assert data["filename"] == test_image.filename
        assert data["dataset_id"] == str(test_image.dataset_id)
        assert data["uploaded_by_id"] == str(test_image.uploaded_by_id)

    async def test_returns_404_for_nonexistent_image(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.get(
            f"/api/images/{fake_id}", headers=analyst_headers
        )
        assert response.status_code == 404


class TestUpdateImage:
    async def test_updates_image_fields(
        self, api_client: AsyncClient, analyst_headers: dict, test_image: Image
    ):
        update_data = {"analyzed": True, "filename": "updated_image.jpg"}

        response = await api_client.patch(
            f"/api/images/{test_image.id}",
            json=update_data,
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analyzed"] is True
        assert data["filename"] == "updated_image.jpg"

        await test_image.refresh_from_db()
        assert test_image.analyzed is True

    async def test_returns_404_for_nonexistent_image(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.patch(
            f"/api/images/{fake_id}",
            json={"analyzed": True},
            headers=analyst_headers,
        )
        assert response.status_code == 404


class TestDeleteImage:
    async def test_deletes_image(
        self, api_client: AsyncClient, admin_headers: dict, test_image: Image
    ):
        image_id = test_image.id

        response = await api_client.delete(
            f"/api/images/{image_id}", headers=admin_headers
        )

        assert response.status_code == 204
        image = await Image.get_or_none(id=image_id)
        assert image is None

    async def test_requires_admin_role(
        self, api_client: AsyncClient, analyst_headers: dict, test_image: Image
    ):
        response = await api_client.delete(
            f"/api/images/{test_image.id}", headers=analyst_headers
        )
        assert response.status_code == 403

    async def test_returns_404_for_nonexistent_image(
        self, api_client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.delete(
            f"/api/images/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404
