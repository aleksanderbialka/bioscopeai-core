"""Unit tests for DatasetCRUD operations."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from bioscopeai_core.app.crud.dataset import DatasetCRUD
from bioscopeai_core.app.models import Dataset, User
from bioscopeai_core.app.schemas.dataset import DatasetCreate, DatasetUpdate


class TestGetUserDatasets:
    """Test user-scoped dataset retrieval."""

    @pytest.fixture
    def crud(self) -> DatasetCRUD:
        return DatasetCRUD()

    async def test_retrieves_only_user_datasets(self, crud: DatasetCRUD, mocker):
        user = User(id=uuid4())
        mock_datasets = [Dataset(), Dataset()]
        mock_filter = mocker.MagicMock()
        mock_filter.prefetch_related = mocker.AsyncMock(return_value=mock_datasets)
        mocker.patch.object(Dataset, "filter", return_value=mock_filter)

        result = await crud.get_user_datasets(user)

        Dataset.filter.assert_called_once_with(owner=user)
        mock_filter.prefetch_related.assert_awaited_once_with("owner")
        assert result == mock_datasets


class TestGetByIdForUser:
    """Test user-scoped dataset retrieval by ID."""

    @pytest.fixture
    def crud(self) -> DatasetCRUD:
        return DatasetCRUD()

    async def test_retrieves_dataset_for_owner(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user = User(id=uuid4())
        mock_dataset = Dataset()
        mock_query = mocker.MagicMock()
        mock_query.prefetch_related = mocker.AsyncMock(return_value=mock_dataset)
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_query)

        result = await crud.get_by_id_for_user(dataset_id, user)

        Dataset.get_or_none.assert_called_once_with(id=dataset_id, owner=user)
        assert result == mock_dataset

    async def test_returns_none_for_non_owner(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user = User(id=uuid4())
        mock_query = mocker.MagicMock()
        mock_query.prefetch_related = mocker.AsyncMock(return_value=None)
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_query)

        result = await crud.get_by_id_for_user(dataset_id, user)

        assert result is None


class TestCreateForUser:
    """Test dataset creation with owner assignment."""

    @pytest.fixture
    def crud(self) -> DatasetCRUD:
        return DatasetCRUD()

    async def test_creates_dataset_with_owner(self, crud: DatasetCRUD, mocker):
        user = User(id=uuid4())
        dataset_data = DatasetCreate(name="Test Dataset", description="Test")
        mock_dataset = Dataset()
        mocker.patch.object(Dataset, "create", return_value=mock_dataset)

        result = await crud.create_for_user(dataset_data, user)

        Dataset.create.assert_called_once_with(
            name="Test Dataset", description="Test", owner=user
        )
        assert result == mock_dataset


class TestUpdateDataset:
    """Test dataset update with authorization."""

    @pytest.fixture
    def crud(self) -> DatasetCRUD:
        return DatasetCRUD()

    async def test_updates_dataset_for_owner(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user = User(id=uuid4())
        mock_dataset = Dataset()
        mock_dataset.save = mocker.AsyncMock()
        mock_dataset.refresh_from_db = mocker.AsyncMock()
        mock_query = mocker.MagicMock()
        mock_query.prefetch_related = mocker.AsyncMock(return_value=mock_dataset)
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_query)

        update_data = DatasetUpdate(name="Updated Name")
        result = await crud.update_dataset(dataset_id, update_data, user)

        assert result == mock_dataset
        assert mock_dataset.name == "Updated Name"
        mock_dataset.save.assert_awaited_once()

    async def test_returns_none_when_not_owner(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user = User(id=uuid4())
        mock_query = mocker.MagicMock()
        mock_query.prefetch_related = mocker.AsyncMock(return_value=None)
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_query)

        result = await crud.update_dataset(dataset_id, DatasetUpdate(name="Test"), user)

        assert result is None


class TestDeleteByIdForUser:
    """Test dataset deletion with authorization."""

    @pytest.fixture
    def crud(self) -> DatasetCRUD:
        return DatasetCRUD()

    async def test_deletes_dataset_for_owner(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user_id = uuid4()
        user = User(id=user_id, is_admin=False)
        mock_dataset = Dataset()
        mock_dataset.owner_id = user_id
        mock_dataset.delete = mocker.AsyncMock()
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_dataset)

        result = await crud.delete_by_id_for_user(dataset_id, user)

        assert result is True
        mock_dataset.delete.assert_awaited_once()

    async def test_raises_404_when_dataset_not_found(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user = User(id=uuid4())
        mocker.patch.object(Dataset, "get_or_none", return_value=mocker.AsyncMock(return_value=None)())

        with pytest.raises(HTTPException) as exc_info:
            await crud.delete_by_id_for_user(dataset_id, user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_raises_403_when_not_owner_and_not_admin(
        self, crud: DatasetCRUD, mocker
    ):
        dataset_id = uuid4()
        user = User(id=uuid4(), is_admin=False)
        mock_dataset = Dataset()
        mock_dataset.owner_id = uuid4()
        mocker.patch.object(Dataset, "get_or_none", return_value=mock_dataset)

        with pytest.raises(HTTPException) as exc_info:
            await crud.delete_by_id_for_user(dataset_id, user)

        assert exc_info.value.status_code == 403
        assert "permission" in exc_info.value.detail.lower()

    async def test_allows_admin_to_delete_any_dataset(self, crud: DatasetCRUD, mocker):
        dataset_id = uuid4()
        user_id = uuid4()
        user = User(id=user_id, is_admin=True)
        mock_dataset = Dataset()
        mock_dataset.owner_id = user_id
        mock_dataset.delete = mocker.AsyncMock()
        mocker.patch.object(Dataset, "get_or_none", return_value=mocker.AsyncMock(return_value=mock_dataset)())

        result = await crud.delete_by_id_for_user(dataset_id, user)

        assert result is True
        mock_dataset.delete.assert_awaited_once()
