"""Unit tests for ClassificationCRUD and ClassificationResultCRUD operations."""

from uuid import uuid4

import pytest

from bioscopeai_core.app.crud.classification import ClassificationCRUD
from bioscopeai_core.app.crud.classification.classification_result import (
    ClassificationResultCRUD,
)
from bioscopeai_core.app.models.classification import (
    Classification,
    ClassificationResult,
    ClassificationStatus,
)
from bioscopeai_core.app.schemas.classification import ClassificationResultCreate


class TestSetStatus:
    """Test classification status updates."""

    @pytest.fixture
    def crud(self) -> ClassificationCRUD:
        return ClassificationCRUD()

    async def test_updates_classification_status(
        self, crud: ClassificationCRUD, mocker
    ):
        classification_id = uuid4()
        mock_classification = Classification()
        mock_classification.status = ClassificationStatus.PENDING
        mock_classification.save = mocker.AsyncMock()
        mocker.patch.object(
            Classification,
            "get_or_none",
            return_value=mocker.AsyncMock(return_value=mock_classification)(),
        )

        result = await crud.set_status(
            ClassificationStatus.COMPLETED, classification_id
        )

        assert result == mock_classification
        assert mock_classification.status == ClassificationStatus.COMPLETED
        mock_classification.save.assert_awaited_once()

    async def test_returns_none_when_not_found(self, crud: ClassificationCRUD, mocker):
        classification_id = uuid4()
        mocker.patch.object(
            Classification,
            "get_or_none",
            return_value=mocker.AsyncMock(return_value=None)(),
        )

        result = await crud.set_status(ClassificationStatus.FAILED, classification_id)

        assert result is None


class TestGetFilteredClassifications:
    """Test classification filtering logic."""

    @pytest.fixture
    def crud(self) -> ClassificationCRUD:
        return ClassificationCRUD()

    async def test_filters_by_status(self, crud: ClassificationCRUD, mocker):
        mock_classifications = [Classification()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_classifications)
        mocker.patch.object(Classification, "filter", return_value=mock_query)

        result = await crud.get_filtered(status="completed")

        Classification.filter.assert_called_once_with(
            status=ClassificationStatus.COMPLETED
        )
        assert result == mock_classifications

    async def test_filters_by_dataset_id(self, crud: ClassificationCRUD, mocker):
        dataset_id = uuid4()
        mock_classifications = [Classification()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_classifications)
        mocker.patch.object(Classification, "filter", return_value=mock_query)

        result = await crud.get_filtered(dataset_id=dataset_id)

        Classification.filter.assert_called_once_with(dataset_id=dataset_id)
        assert result == mock_classifications

    async def test_filters_by_image_id(self, crud: ClassificationCRUD, mocker):
        image_id = uuid4()
        mock_classifications = [Classification()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_classifications)
        mocker.patch.object(Classification, "filter", return_value=mock_query)

        result = await crud.get_filtered(image_id=image_id)

        Classification.filter.assert_called_once_with(image_id=image_id)
        assert result == mock_classifications

    async def test_filters_by_created_by(self, crud: ClassificationCRUD, mocker):
        user_id = uuid4()
        mock_classifications = [Classification()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_classifications)
        mocker.patch.object(Classification, "filter", return_value=mock_query)

        result = await crud.get_filtered(created_by=user_id)

        Classification.filter.assert_called_once_with(created_by_id=user_id)
        assert result == mock_classifications


class TestCreateResult:
    """Test classification result creation."""

    @pytest.fixture
    def crud(self) -> ClassificationResultCRUD:
        return ClassificationResultCRUD()

    async def test_creates_result_with_provided_data(
        self, crud: ClassificationResultCRUD, mocker
    ):
        result_data = ClassificationResultCreate(
            image_id=uuid4(),
            classification_id=uuid4(),
            label="positive",
            confidence=0.95,
            model_name="resnet50",
        )
        mock_result = ClassificationResult()
        mocker.patch.object(ClassificationResult, "create", return_value=mock_result)

        result = await crud.create_result(result_data)

        assert result == mock_result


class TestGetFilteredResults:
    """Test classification result filtering."""

    @pytest.fixture
    def crud(self) -> ClassificationResultCRUD:
        return ClassificationResultCRUD()

    async def test_filters_by_classification_id(
        self, crud: ClassificationResultCRUD, mocker
    ):
        classification_id = uuid4()
        mock_results = [ClassificationResult()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_results)
        mocker.patch.object(ClassificationResult, "filter", return_value=mock_query)

        result = await crud.get_by_classification(classification_id)

        ClassificationResult.filter.assert_called_once_with(
            classification_id=classification_id
        )
        assert result == mock_results

    async def test_filters_by_image_id(self, crud: ClassificationResultCRUD, mocker):
        image_id = uuid4()
        mock_results = [ClassificationResult()]
        mock_query = mocker.MagicMock()
        mock_query.order_by = mocker.AsyncMock(return_value=mock_results)
        mocker.patch.object(ClassificationResult, "filter", return_value=mock_query)

        result = await crud.get_by_image(image_id)

        ClassificationResult.filter.assert_called_once_with(image_id=image_id)
        assert result == mock_results
