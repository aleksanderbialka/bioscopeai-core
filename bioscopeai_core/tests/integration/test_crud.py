"""Integration tests for CRUD operations with database."""

from uuid import uuid4

import pytest

from bioscopeai_core.app.crud.classification import ClassificationCRUD
from bioscopeai_core.app.crud.classification.classification_result import (
    ClassificationResultCRUD,
)
from bioscopeai_core.app.crud.dataset import DatasetCRUD
from bioscopeai_core.app.crud.device import DeviceCRUD
from bioscopeai_core.app.crud.image import ImageCRUD
from bioscopeai_core.app.models import (
    Classification,
    ClassificationResult,
    Dataset,
    Device,
    Image,
    User,
)
from bioscopeai_core.app.models.classification import ClassificationStatus
from bioscopeai_core.app.models.users import UserRole, UserStatus
from bioscopeai_core.app.schemas.classification import (
    ClassificationCreate,
    ClassificationResultCreate,
)
from bioscopeai_core.app.schemas.dataset import DatasetCreate, DatasetUpdate
from bioscopeai_core.app.schemas.device import DeviceCreate, DeviceUpdate
from bioscopeai_core.app.schemas.image import ImageUpdate


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


class TestImageCRUDLifecycle:
    """Test complete image CRUD lifecycle with database."""

    async def test_update_and_mark_analyzed(self, db, test_user: User):
        crud = ImageCRUD()
        dataset_crud = DatasetCRUD()
        dataset = await dataset_crud.create_for_user(
            DatasetCreate(name="Test Dataset"), test_user
        )

        image = await Image.create(
            filename="test.jpg",
            filepath="/uploads/test.jpg",
            dataset_id=dataset.id,
            uploaded_by_id=test_user.id,
        )

        assert image.analyzed is False

        update_data = ImageUpdate(analyzed=True)
        updated = await crud.update_image(image.id, update_data)
        assert updated is not None
        assert updated.analyzed is True

        marked = await crud.mark_as_analyzed(image.id)
        assert marked is not None
        assert marked.analyzed is True


class TestClassificationCRUDLifecycle:
    """Test complete classification CRUD lifecycle with database."""

    async def test_status_updates(self, db, test_user: User):
        crud = ClassificationCRUD()
        dataset_crud = DatasetCRUD()
        dataset = await dataset_crud.create_for_user(
            DatasetCreate(name="Test Dataset"), test_user
        )

        classification = await Classification.create(
            dataset_id=dataset.id,
            model_name="resnet50",
            created_by_id=test_user.id,
            status=ClassificationStatus.PENDING,
        )

        assert classification.status == ClassificationStatus.PENDING

        updated = await crud.set_status(ClassificationStatus.RUNNING, classification.id)
        assert updated is not None
        assert updated.status == ClassificationStatus.RUNNING

        completed = await crud.set_status(
            ClassificationStatus.COMPLETED, classification.id
        )
        assert completed is not None
        assert completed.status == ClassificationStatus.COMPLETED


class TestClassificationResultCRUDLifecycle:
    """Test classification result CRUD lifecycle with database."""

    async def test_create_and_retrieve_results(self, db, test_user: User):
        crud = ClassificationResultCRUD()
        dataset_crud = DatasetCRUD()
        dataset = await dataset_crud.create_for_user(
            DatasetCreate(name="Test Dataset"), test_user
        )

        image = await Image.create(
            filename="test.jpg",
            filepath="/uploads/test.jpg",
            dataset_id=dataset.id,
            uploaded_by_id=test_user.id,
        )

        classification = await Classification.create(
            dataset_id=dataset.id,
            image_id=image.id,
            model_name="resnet50",
            created_by_id=test_user.id,
        )

        result_data = ClassificationResultCreate(
            image_id=image.id,
            classification_id=classification.id,
            label="positive",
            confidence=0.95,
            model_name="resnet50",
        )

        created = await crud.create_result(result_data)
        assert created.id is not None
        assert created.label == "positive"
        assert created.confidence == 0.95

        by_classification = await crud.get_by_classification(classification.id)
        assert len(by_classification) == 1
        assert by_classification[0].id == created.id

        by_image = await crud.get_by_image(image.id)
        assert len(by_image) == 1
        assert by_image[0].id == created.id
