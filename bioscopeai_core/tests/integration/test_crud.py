"""Integration tests for CRUD operations with database."""

from uuid import uuid4

import pytest

from bioscopeai_core.app.crud.dataset import DatasetCRUD
from bioscopeai_core.app.crud.device import DeviceCRUD
from bioscopeai_core.app.models import Dataset, Device, User
from bioscopeai_core.app.models.users import UserRole, UserStatus
from bioscopeai_core.app.schemas.dataset import DatasetCreate, DatasetUpdate
from bioscopeai_core.app.schemas.device import DeviceCreate, DeviceUpdate


@pytest.fixture
async def test_user(db) -> User:
    """Create test user."""
    return await User.create(
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        first_name="Test",
        last_name="User",
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
    )


class TestDeviceCRUDLifecycle:
    """Test complete device CRUD lifecycle with database."""

    async def test_create_retrieve_update_delete_device(self, db):
        crud = DeviceCRUD()
        device_data = DeviceCreate(
            name="Microscope-01",
            hostname="mic-01.lab.local",
            location="Lab A",
            firmware_version="1.0.0",
        )

        created = await crud.create_device(device_data)
        assert created.id is not None
        assert created.name == "Microscope-01"
        assert created.is_online is False

        retrieved = await crud.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == "Microscope-01"

        update_data = DeviceUpdate(location="Lab B", is_online=True)
        updated = await crud.update_device(created.id, update_data)
        assert updated is not None
        assert updated.location == "Lab B"
        assert updated.name == "Microscope-01"

        deleted = await crud.delete_by_id(created.id)
        assert deleted is True
        assert await crud.get_by_id(created.id) is None


class TestDatasetCRUDLifecycle:
    """Test complete dataset CRUD lifecycle with database."""

    async def test_create_retrieve_update_delete_dataset(self, db, test_user: User):
        crud = DatasetCRUD()
        dataset_data = DatasetCreate(name="Test Dataset", description="Test desc")

        created = await crud.create_for_user(dataset_data, test_user)
        assert created.id is not None
        assert created.name == "Test Dataset"
        assert created.owner_id == test_user.id

        retrieved = await crud.get_by_id_for_user(created.id, test_user)
        assert retrieved is not None
        assert retrieved.name == "Test Dataset"

        update_data = DatasetUpdate(description="Updated description")
        updated = await crud.update_dataset(created.id, update_data, test_user)
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.name == "Test Dataset"

        deleted = await crud.delete_by_id_for_user(created.id, test_user)
        assert deleted is True
        assert await crud.get_by_id_for_user(created.id, test_user) is None
