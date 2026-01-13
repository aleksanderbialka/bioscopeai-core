"""Unit tests for DeviceCRUD operations."""

from uuid import uuid4

import pytest

from bioscopeai_core.app.crud.device import DeviceCRUD
from bioscopeai_core.app.models.device import Device
from bioscopeai_core.app.schemas.device import DeviceCreate, DeviceUpdate


class TestGetFilteredDevices:
    """Test device filtering logic."""

    @pytest.fixture
    def crud(self) -> DeviceCRUD:
        return DeviceCRUD()

    async def test_no_filters_returns_all(self, crud: DeviceCRUD, mocker):
        mock_devices = [Device(), Device()]
        mocker.patch.object(Device, "filter", return_value=mocker.AsyncMock(return_value=mock_devices)())

        result = await crud.get_filtered_devices()

        assert result == mock_devices

    @pytest.mark.parametrize(
        "is_online,expected_filter",
        [(True, {"is_online": True}), (False, {"is_online": False})],
    )
    async def test_filter_by_online_status(
        self, crud: DeviceCRUD, mocker, is_online: bool, expected_filter: dict
    ):
        mock_devices = [Device()]
        mocker.patch.object(Device, "filter", return_value=mocker.AsyncMock(return_value=mock_devices)())

        result = await crud.get_filtered_devices(is_online=is_online)

        assert result == mock_devices

    async def test_filter_by_location(self, crud: DeviceCRUD, mocker):
        mock_devices = [Device()]
        mocker.patch.object(Device, "filter", return_value=mocker.AsyncMock(return_value=mock_devices)())

        result = await crud.get_filtered_devices(location="Lab A")

        assert result == mock_devices

    async def test_filter_by_multiple_criteria(self, crud: DeviceCRUD, mocker):
        mock_devices = [Device()]
        mocker.patch.object(Device, "filter", return_value=mocker.AsyncMock(return_value=mock_devices)())

        result = await crud.get_filtered_devices(is_online=True, location="Lab B")

        assert result == mock_devices


class TestCreateDevice:
    """Test device creation logic."""

    @pytest.fixture
    def crud(self) -> DeviceCRUD:
        return DeviceCRUD()

    async def test_creates_device_with_provided_data(self, crud: DeviceCRUD, mocker):
        device_data = DeviceCreate(
            name="Microscope-01", hostname="mic-01.local", location="Lab A"
        )
        mock_device = Device()
        mocker.patch.object(Device, "create", return_value=mock_device)

        result = await crud.create_device(device_data)

        assert result == mock_device


class TestUpdateDevice:
    """Test device update logic."""

    @pytest.fixture
    def crud(self) -> DeviceCRUD:
        return DeviceCRUD()

    async def test_updates_device_fields(self, crud: DeviceCRUD, mocker):
        device_id = uuid4()
        mock_device = Device()
        mock_device.save = mocker.AsyncMock()
        mock_device.refresh_from_db = mocker.AsyncMock()
        mocker.patch.object(Device, "get_or_none", return_value=mock_device)

        update_data = DeviceUpdate(name="Updated Name", location="Lab C")
        result = await crud.update_device(device_id, update_data)

        assert result == mock_device
        assert mock_device.name == "Updated Name"
        assert mock_device.location == "Lab C"
        mock_device.save.assert_awaited_once()
        mock_device.refresh_from_db.assert_awaited_once()

    async def test_partial_update_only_sets_provided_fields(
        self, crud: DeviceCRUD, mocker
    ):
        device_id = uuid4()
        mock_device = Device()
        mock_device.name = "Original Name"
        mock_device.location = "Original Location"
        mock_device.save = mocker.AsyncMock()
        mock_device.refresh_from_db = mocker.AsyncMock()
        mocker.patch.object(Device, "get_or_none", return_value=mock_device)

        update_data = DeviceUpdate(location="New Location")
        await crud.update_device(device_id, update_data)

        assert mock_device.location == "New Location"
        assert mock_device.name == "Original Name"

    async def test_returns_none_when_device_not_found(self, crud: DeviceCRUD, mocker):
        device_id = uuid4()
        mocker.patch.object(Device, "get_or_none", return_value=mocker.AsyncMock(return_value=None)())

        result = await crud.update_device(device_id, DeviceUpdate(name="Test"))

        assert result is None
