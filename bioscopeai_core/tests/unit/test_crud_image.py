"""Unit tests for ImageCRUD operations."""

from datetime import datetime, UTC
from uuid import uuid4

import pytest
from fastapi import HTTPException

from bioscopeai_core.app.crud.image import ImageCRUD
from bioscopeai_core.app.models.image import Image
from bioscopeai_core.app.schemas.image import ImageUpdate


class TestGetFilteredImages:
    """Test image filtering logic."""

    @pytest.fixture
    def crud(self) -> ImageCRUD:
        return ImageCRUD()

    async def test_filters_by_dataset_id(self, crud: ImageCRUD, mocker):
        dataset_id = uuid4()
        mock_images = [Image(), Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        result = await crud.get_filtered_images(dataset_id=dataset_id)

        Image.filter.assert_called_once_with(dataset_id=dataset_id)
        assert result == mock_images

    async def test_filters_by_device_id(self, crud: ImageCRUD, mocker):
        device_id = uuid4()
        mock_images = [Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        result = await crud.get_filtered_images(device_id=device_id)

        Image.filter.assert_called_once_with(device_id=device_id)
        assert result == mock_images

    async def test_filters_by_analyzed_status(self, crud: ImageCRUD, mocker):
        mock_images = [Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        result = await crud.get_filtered_images(analyzed=True)

        Image.filter.assert_called_once_with(analyzed=True)
        assert result == mock_images

    async def test_filters_by_date_range(self, crud: ImageCRUD, mocker):
        created_from = datetime(2024, 1, 1, tzinfo=UTC)
        created_to = datetime(2024, 12, 31, tzinfo=UTC)
        mock_images = [Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        result = await crud.get_filtered_images(
            created_from=created_from, created_to=created_to
        )

        Image.filter.assert_called_once_with(
            uploaded_at__gte=created_from, uploaded_at__lte=created_to
        )
        assert result == mock_images

    async def test_search_by_filename(self, crud: ImageCRUD, mocker):
        mock_images = [Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        result = await crud.get_filtered_images(q="microscope")

        Image.filter.assert_called_once_with(filename__icontains="microscope")
        assert result == mock_images

    async def test_pagination_offset_and_limit(self, crud: ImageCRUD, mocker):
        mock_images = [Image()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.MagicMock(return_value=mock_query)
        mock_query.offset = mocker.MagicMock(return_value=mock_query)
        mock_query.limit = mocker.AsyncMock(return_value=mock_images)
        mocker.patch.object(Image, "filter", return_value=mock_query)

        await crud.get_filtered_images(page=3, page_size=10)

        mock_query.offset.assert_called_once_with(20)
        mock_query.limit.assert_called_once_with(10)

    async def test_raises_400_for_invalid_order_field(self, crud: ImageCRUD, mocker):
        mocker.patch.object(Image, "filter")

        with pytest.raises(HTTPException) as exc_info:
            await crud.get_filtered_images(order_by="invalid_field")

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()


class TestUpdateImage:
    """Test image update logic."""

    @pytest.fixture
    def crud(self) -> ImageCRUD:
        return ImageCRUD()

    async def test_updates_image_fields(self, crud: ImageCRUD, mocker):
        image_id = uuid4()
        mock_image = Image()
        mock_image.save = mocker.AsyncMock()
        mock_image.refresh_from_db = mocker.AsyncMock()
        mocker.patch.object(
            Image, "get_or_none", return_value=mocker.AsyncMock(return_value=mock_image)()
        )

        update_data = ImageUpdate(analyzed=True)
        result = await crud.update_image(image_id, update_data)

        assert result == mock_image
        assert mock_image.analyzed is True
        mock_image.save.assert_awaited_once()

    async def test_returns_none_when_image_not_found(self, crud: ImageCRUD, mocker):
        image_id = uuid4()
        mocker.patch.object(
            Image, "get_or_none", return_value=mocker.AsyncMock(return_value=None)()
        )

        result = await crud.update_image(image_id, ImageUpdate(analyzed=True))

        assert result is None


class TestMarkAsAnalyzed:
    """Test marking image as analyzed."""

    @pytest.fixture
    def crud(self) -> ImageCRUD:
        return ImageCRUD()

    async def test_marks_image_as_analyzed(self, crud: ImageCRUD, mocker):
        image_id = uuid4()
        mock_image = Image()
        mock_image.analyzed = False
        mock_image.save = mocker.AsyncMock()
        mock_image.refresh_from_db = mocker.AsyncMock()
        mocker.patch.object(
            Image, "get_or_none", return_value=mocker.AsyncMock(return_value=mock_image)()
        )

        result = await crud.mark_as_analyzed(image_id)

        assert result == mock_image
        assert mock_image.analyzed is True
        mock_image.save.assert_awaited_once()

    async def test_returns_none_when_image_not_found(self, crud: ImageCRUD, mocker):
        image_id = uuid4()
        mocker.patch.object(
            Image, "get_or_none", return_value=mocker.AsyncMock(return_value=None)()
        )

        result = await crud.mark_as_analyzed(image_id)

        assert result is None
