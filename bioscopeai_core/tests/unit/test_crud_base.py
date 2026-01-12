"""Unit tests for BaseCRUD operations."""

from typing import cast
from uuid import uuid4

import pytest
from tortoise.models import Model

from bioscopeai_core.app.crud.base import BaseCRUD


class MockModel(Model):
    """Mock Tortoise model for testing."""

    class Meta:
        abstract = True


class TestBaseCRUD:
    """Test BaseCRUD operations with mocked database calls."""

    @pytest.fixture
    def crud(self) -> BaseCRUD[MockModel]:
        crud = BaseCRUD[MockModel]()
        crud.model = MockModel
        return crud

    async def test_get_all_returns_list(self, crud: BaseCRUD[MockModel], mocker):
        mock_objs = [MockModel(), MockModel()]
        mocker.patch.object(MockModel, "all", return_value=mocker.AsyncMock(return_value=mock_objs)())

        result = await crud.get_all()

        assert result == mock_objs

    async def test_get_by_id_returns_object(self, crud: BaseCRUD[MockModel], mocker):
        obj_id = uuid4()
        mock_obj = MockModel()
        mocker.patch.object(MockModel, "get_or_none", return_value=mock_obj)

        result = await crud.get_by_id(obj_id)

        assert result == mock_obj
        MockModel.get_or_none.assert_called_once_with(id=obj_id)

    async def test_get_by_id_returns_none_when_not_found(
        self, crud: BaseCRUD[MockModel], mocker
    ):
        obj_id = uuid4()
        mocker.patch.object(MockModel, "get_or_none", return_value=mocker.AsyncMock(return_value=None)())

        result = await crud.get_by_id(obj_id)

        assert result is None

    async def test_delete_by_id_returns_true_when_deleted(
        self, crud: BaseCRUD[MockModel], mocker
    ):
        obj_id = uuid4()
        mock_obj = MockModel()
        mock_obj.delete = mocker.AsyncMock()
        mocker.patch.object(MockModel, "get_or_none", return_value=mock_obj)

        result = await crud.delete_by_id(obj_id)

        assert result is True
        mock_obj.delete.assert_awaited_once()

    async def test_delete_by_id_returns_false_when_not_found(
        self, crud: BaseCRUD[MockModel], mocker
    ):
        obj_id = uuid4()
        mocker.patch.object(MockModel, "get_or_none", return_value=mocker.AsyncMock(return_value=None)())

        result = await crud.delete_by_id(obj_id)

        assert result is False
