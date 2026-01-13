"""Integration tests for device API endpoints."""

import pytest
from httpx import AsyncClient

from bioscopeai_core.app.models import User
from bioscopeai_core.app.models.device.device import Device
from bioscopeai_core.app.models.users.user import UserRole
from bioscopeai_core.tests.conftest import (
    TEST_PASSWORD,
    create_test_user,
    get_auth_token,
)


@pytest.fixture
async def viewer_user_with_password() -> User:
    return await create_test_user("viewer@example.com", "viewer", UserRole.VIEWER, TEST_PASSWORD)


@pytest.fixture
async def analyst_user_with_password() -> User:
    return await create_test_user("analyst@example.com", "analyst", UserRole.ANALYST, TEST_PASSWORD)


@pytest.fixture
async def admin_user_with_password() -> User:
    return await create_test_user("admin@example.com", "adminuser", UserRole.ADMIN, "AdminPass123!")


@pytest.fixture
async def admin_user_with_password() -> User:
    return await create_test_user("admin@example.com", "admin", UserRole.ADMIN, TEST_PASSWORD)


@pytest.fixture
async def get_viewer_token(api_client: AsyncClient, viewer_user_with_password: User) -> str:
    return await get_auth_token(api_client, viewer_user_with_password.email, TEST_PASSWORD)


@pytest.fixture
async def get_analyst_token(api_client: AsyncClient, analyst_user_with_password: User) -> str:
    return await get_auth_token(api_client, analyst_user_with_password.email, TEST_PASSWORD)


@pytest.fixture
async def get_admin_token(api_client: AsyncClient, admin_user_with_password: User) -> str:
    return await get_auth_token(api_client, admin_user_with_password.email, TEST_PASSWORD)


@pytest.fixture
async def sample_device() -> Device:
    return await Device.create(
        name="Test Device 001",
        hostname="test-device-001",
        location="Lab A",
        is_online=True,
        firmware_version="1.0.0",
    )


@pytest.fixture
def valid_device_data() -> dict:
    return {
        "name": "New Device",
        "hostname": "new-device-001",
        "location": "Lab C",
        "firmware_version": "1.0.0",
    }


class TestListDevices:

    async def test_list_devices_analyst_access(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_analyst_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get("/api/devices/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["hostname"] == sample_device.hostname

    async def test_list_devices_requires_analyst_role(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_viewer_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_viewer_token}"}
        response = await api_client.get("/api/devices/", headers=headers)
        assert response.status_code == 403

    async def test_list_devices_requires_authentication(
        self, api_client: AsyncClient, sample_device: Device
    ):
        response = await api_client.get("/api/devices/")
        assert response.status_code == 401

    async def test_list_devices_filter_by_online_status(
        self, api_client: AsyncClient, get_analyst_token: str
    ):
        await Device.create(
            name="Online Device",
            hostname="online-device",
            location="Lab A",
            is_online=True,
        )
        await Device.create(
            name="Offline Device",
            hostname="offline-device",
            location="Lab B",
            is_online=False,
        )

        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get(
            "/api/devices/", params={"is_online": "true"}, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(device["is_online"] is True for device in data)

    async def test_list_devices_filter_by_location(
        self, api_client: AsyncClient, get_analyst_token: str
    ):
        await Device.create(
            name="Device A",
            hostname="device-a",
            location="Lab A",
            is_online=True,
        )
        await Device.create(
            name="Device B",
            hostname="device-b",
            location="Lab B",
            is_online=True,
        )

        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get(
            "/api/devices/", params={"location": "Lab A"}, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(device["location"] == "Lab A" for device in data)

    async def test_list_devices_with_multiple_filters(
        self, api_client: AsyncClient, get_analyst_token: str
    ):
        await Device.create(
            name="Device A",
            hostname="device-a",
            location="Lab A",
            is_online=True,
        )
        await Device.create(
            name="Device B",
            hostname="device-b",
            location="Lab A",
            is_online=False,
        )

        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get(
            "/api/devices/",
            params={"is_online": "true", "location": "Lab A"},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(
            device["is_online"] is True and device["location"] == "Lab A"
            for device in data
        )


class TestGetDevice:
    async def test_get_device_by_id(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_analyst_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get(
            f"/api/devices/{sample_device.id}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hostname"] == sample_device.hostname
        assert data["location"] == sample_device.location

    async def test_get_nonexistent_device_returns_404(
        self, api_client: AsyncClient, get_analyst_token: str
    ):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.get(f"/api/devices/{fake_uuid}", headers=headers)
        assert response.status_code == 404

    async def test_get_device_requires_authentication(
        self, api_client: AsyncClient, sample_device: Device
    ):
        response = await api_client.get(f"/api/devices/{sample_device.id}")
        assert response.status_code == 401


class TestCreateDevice:
    async def test_create_device_admin_success(
        self,
        api_client: AsyncClient,
        valid_device_data: dict,
        get_admin_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        response = await api_client.post(
            "/api/devices/", json=valid_device_data, headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == valid_device_data["name"]
        assert "id" in data

        device = await Device.get_or_none(hostname=valid_device_data["hostname"])
        assert device is not None

    async def test_create_device_requires_admin_role(
        self,
        api_client: AsyncClient,
        valid_device_data: dict,
        get_analyst_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.post(
            "/api/devices/", json=valid_device_data, headers=headers
        )
        assert response.status_code == 403

    async def test_create_device_validates_required_fields(
        self, api_client: AsyncClient, get_admin_token: str
    ):
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        invalid_data = {"location": "Lab A"}
        response = await api_client.post(
            "/api/devices/", json=invalid_data, headers=headers
        )
        assert response.status_code == 422

    async def test_create_device_requires_authentication(
        self, api_client: AsyncClient, valid_device_data: dict
    ):
        response = await api_client.post("/api/devices/", json=valid_device_data)
        assert response.status_code == 401


class TestUpdateDevice:
    async def test_update_device_admin_success(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_admin_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        update_data = {"name": "Updated Device", "location": "Updated Location"}

        response = await api_client.patch(
            f"/api/devices/{sample_device.id}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Device"
        assert data["location"] == "Updated Location"

    async def test_update_device_partial_update(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_admin_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        update_data = {"location": "New Lab"}

        response = await api_client.patch(
            f"/api/devices/{sample_device.id}", json=update_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "New Lab"
        assert data["name"] == sample_device.name

    async def test_update_device_requires_admin_role(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_analyst_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        update_data = {"name": "Hacked Device"}
        response = await api_client.patch(
            f"/api/devices/{sample_device.id}", json=update_data, headers=headers
        )
        assert response.status_code == 403

    async def test_update_nonexistent_device_returns_404(
        self, api_client: AsyncClient, get_admin_token: str
    ):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        update_data = {"name": "Ghost Device"}
        response = await api_client.patch(
            f"/api/devices/{fake_uuid}", json=update_data, headers=headers
        )
        assert response.status_code == 404


class TestDeleteDevice:
    async def test_delete_device_admin_success(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_admin_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        response = await api_client.delete(
            f"/api/devices/{sample_device.id}", headers=headers
        )
        assert response.status_code == 204

        device = await Device.get_or_none(id=sample_device.id)
        assert device is None

    async def test_delete_device_requires_admin_role(
        self,
        api_client: AsyncClient,
        sample_device: Device,
        get_analyst_token: str,
    ):
        headers = {"Authorization": f"Bearer {get_analyst_token}"}
        response = await api_client.delete(
            f"/api/devices/{sample_device.id}", headers=headers
        )
        assert response.status_code == 403

    async def test_delete_nonexistent_device_returns_404(
        self, api_client: AsyncClient, get_admin_token: str
    ):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        headers = {"Authorization": f"Bearer {get_admin_token}"}
        response = await api_client.delete(f"/api/devices/{fake_uuid}", headers=headers)
        assert response.status_code == 404

    async def test_delete_device_requires_authentication(
        self, api_client: AsyncClient, sample_device: Device
    ):
        response = await api_client.delete(f"/api/devices/{sample_device.id}")
        assert response.status_code == 401
