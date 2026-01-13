"""Integration tests for classification API endpoints."""

import pytest
from httpx import AsyncClient
from uuid import UUID
from unittest.mock import AsyncMock, patch

from bioscopeai_core.app.models import User, Dataset, Image, Device
from bioscopeai_core.app.models.classification import Classification
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
        description="Dataset for classification tests",
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
    )


@pytest.fixture
async def test_classification(analyst_user: User, test_image: Image) -> Classification:
    return await Classification.create(
        image=test_image,
        model_name="test_model",
        created_by=analyst_user,
        status="pending",
    )


class TestRunClassification:
    @patch("bioscopeai_core.app.crud.classification.classification.get_classification_producer")
    async def test_creates_classification_for_image(
        self,
        mock_producer: AsyncMock,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_image: Image,
    ):
        mock_instance = AsyncMock()
        mock_instance.send_event = AsyncMock()
        mock_producer.return_value = mock_instance

        classification_data = {
            "image_id": str(test_image.id),
            "model_name": "resnet50",
        }

        response = await api_client.post(
            "/api/classifications/run",
            json=classification_data,
            headers=analyst_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert UUID(data["id"])

        classification = await Classification.get_or_none(id=data["id"])
        assert classification is not None
        assert classification.image_id == test_image.id
        assert classification.model_name == "resnet50"
        mock_instance.send_event.assert_called_once()

    @patch("bioscopeai_core.app.crud.classification.classification.get_classification_producer")
    async def test_creates_classification_for_dataset(
        self,
        mock_producer: AsyncMock,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_dataset: Dataset,
    ):
        mock_instance = AsyncMock()
        mock_instance.send_event = AsyncMock()
        mock_producer.return_value = mock_instance

        classification_data = {
            "dataset_id": str(test_dataset.id),
            "model_name": "vgg16",
        }

        response = await api_client.post(
            "/api/classifications/run",
            json=classification_data,
            headers=analyst_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        classification = await Classification.get_or_none(id=data["id"])
        assert classification is not None
        assert classification.dataset_id == test_dataset.id
        mock_instance.send_event.assert_called_once()

    async def test_rejects_both_image_and_dataset(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_image: Image,
        test_dataset: Dataset,
    ):
        classification_data = {
            "image_id": str(test_image.id),
            "dataset_id": str(test_dataset.id),
            "model_name": "resnet50",
        }

        response = await api_client.post(
            "/api/classifications/run",
            json=classification_data,
            headers=analyst_headers,
        )

        assert response.status_code == 400
        assert "exactly one" in response.json()["detail"].lower()

    async def test_rejects_neither_image_nor_dataset(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        classification_data = {"model_name": "resnet50"}

        response = await api_client.post(
            "/api/classifications/run",
            json=classification_data,
            headers=analyst_headers,
        )

        assert response.status_code == 400

    async def test_requires_analyst_role(
        self, api_client: AsyncClient, test_image: Image
    ):
        viewer = await User.create_user(
            email="viewer@test.example.com",
            username="viewer",
            first_name="Test",
            last_name="Viewer",
            password="ViewerPass123!",
        )
        token = await get_auth_token(api_client, viewer.email, "ViewerPass123!")
        headers = {"Authorization": f"Bearer {token}"}

        classification_data = {
            "image_id": str(test_image.id),
            "model_name": "resnet50",
        }

        response = await api_client.post(
            "/api/classifications/run",
            json=classification_data,
            headers=headers,
        )
        assert response.status_code == 403


class TestListClassifications:
    async def test_returns_classifications_list(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_classification: Classification,
    ):
        response = await api_client.get(
            "/api/classifications/", headers=analyst_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(test_classification.id)

    async def test_filters_by_status(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        analyst_user: User,
        test_image: Image,
    ):
        await Classification.create(
            image=test_image,
            model_name="model1",
            created_by=analyst_user,
            status="pending",
        )
        await Classification.create(
            image=test_image,
            model_name="model2",
            created_by=analyst_user,
            status="completed",
        )

        response = await api_client.get(
            "/api/classifications/?status_filter=completed",
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    async def test_filters_by_dataset_id(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        analyst_user: User,
        test_dataset: Dataset,
    ):
        classification = await Classification.create(
            dataset=test_dataset,
            model_name="model1",
            created_by=analyst_user,
            status="pending",
        )

        response = await api_client.get(
            f"/api/classifications/?dataset_id={test_dataset.id}",
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(classification.id)

    async def test_filters_by_image_id(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_image: Image,
        test_classification: Classification,
    ):
        response = await api_client.get(
            f"/api/classifications/?image_id={test_image.id}",
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(test_classification.id)


class TestGetClassification:
    async def test_returns_classification_details(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_classification: Classification,
    ):
        response = await api_client.get(
            f"/api/classifications/{test_classification.id}",
            headers=analyst_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_classification.id)
        assert data["model_name"] == test_classification.model_name
        assert data["status"] == test_classification.status

    async def test_returns_404_for_nonexistent_classification(
        self, api_client: AsyncClient, analyst_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.get(
            f"/api/classifications/{fake_id}", headers=analyst_headers
        )
        assert response.status_code == 404


class TestDeleteClassification:
    async def test_deletes_classification(
        self,
        api_client: AsyncClient,
        admin_headers: dict,
        test_classification: Classification,
    ):
        classification_id = test_classification.id

        response = await api_client.delete(
            f"/api/classifications/{classification_id}", headers=admin_headers
        )

        assert response.status_code == 204
        classification = await Classification.get_or_none(id=classification_id)
        assert classification is None

    async def test_requires_admin_role(
        self,
        api_client: AsyncClient,
        analyst_headers: dict,
        test_classification: Classification,
    ):
        response = await api_client.delete(
            f"/api/classifications/{test_classification.id}", headers=analyst_headers
        )
        assert response.status_code == 403

    async def test_returns_404_for_nonexistent_classification(
        self, api_client: AsyncClient, admin_headers: dict
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await api_client.delete(
            f"/api/classifications/{fake_id}", headers=admin_headers
        )
        assert response.status_code == 404
