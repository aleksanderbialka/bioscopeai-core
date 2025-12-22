from typing import TYPE_CHECKING

from loguru import logger


if TYPE_CHECKING:
    from bioscopeai_core.app.schemas.classification import ClassificationResultCreate


from bioscopeai_core.app.crud.classification import (
    ClassificationCRUD,
    ClassificationResultCRUD,
    get_classification_crud,
    get_classification_result_crud,
)
from bioscopeai_core.app.crud.image import get_image_crud, ImageCRUD
from bioscopeai_core.app.models.classification import ClassificationStatus
from bioscopeai_core.app.serializers.classification.classification_result import (
    ClassificationResultSerializer,
    get_classification_result_serializer,
)


class ClassificationResultService:
    """Service for processing classification results."""

    def __init__(self) -> None:
        self.classification_result_crud: ClassificationResultCRUD = (
            get_classification_result_crud()
        )
        self.classification_crud: ClassificationCRUD = get_classification_crud()
        self.classification_result_serializer: ClassificationResultSerializer = (
            get_classification_result_serializer()
        )
        self.image_crud: ImageCRUD = get_image_crud()

    async def process_classification_result(
        self, classification_result_event: str
    ) -> None:
        """Process a single classification result message."""
        try:
            classification_result: ClassificationResultCreate = (
                self.classification_result_serializer.create_from_event(
                    classification_result_event=classification_result_event
                )
            )
        except ValueError:
            logger.exception(
                f"Invalid classification result event: {classification_result_event}"
            )
            raise
        else:
            logger.info(
                f"Processing classification result: {classification_result.classification_id}"
            )
        try:
            await self.classification_result_crud.create_result(
                data=classification_result
            )
            if classification_result.classification_id is not None:
                await self.classification_crud.set_status(
                    classification_id=classification_result.classification_id,
                    status=ClassificationStatus.COMPLETED,
                )
                await self.image_crud.mark_as_analyzed(
                    image_id=classification_result.image_id
                )
        except Exception:
            logger.exception(
                f"Failed to process classification result: {classification_result_event}"
            )
            raise
        else:
            logger.info(
                "Completed processing classification result: "
                f"{classification_result.classification_id}"
            )


def get_classification_result_service() -> ClassificationResultService:
    return ClassificationResultService()
