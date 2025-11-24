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
            logger.info(
                f"Processing classification result: {classification_result.classification_id}"
            )
            await self.classification_result_crud.create_result(
                data=classification_result
            )
            await self.classification_crud.set_status(
                classification_id=classification_result.classification_id,
                status=ClassificationStatus.COMPLETED,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                f"Failed to process classification result: {classification_result_event}"
            )
        else:
            logger.info(
                "Completed processing classification result: "
                f"{classification_result.classification_id}"
            )


def get_classification_result_service() -> ClassificationResultService:
    return ClassificationResultService()
