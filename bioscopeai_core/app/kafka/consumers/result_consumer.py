from loguru import logger

from bioscopeai_core.app.services.classification_result import (
    ClassificationResultService,
    get_classification_result_service,
)

from .base_consumer import BaseKafkaConsumer


class ClassificationResultConsumer(BaseKafkaConsumer):
    """Kafka consumer for classification results."""

    def __init__(self) -> None:
        super().__init__()
        self.classification_result_service: ClassificationResultService = (
            get_classification_result_service()
        )

    async def process_message(self, message: str) -> None:
        """Process a single classification result message."""
        try:
            await self.classification_result_service.process_classification_result(
                classification_result_event=message
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to process classification result message")
        else:
            await self.commit_message()

    def _get_topic_name(self) -> str:
        return self.kafka_settings.CLASSIFICATION_RESULTS_TOPIC

    def _get_group_id(self) -> str:
        return self.kafka_settings.CLASSIFICATION_CONSUMER_GROUP


def get_classification_result_consumer() -> ClassificationResultConsumer:
    """Get the singleton instance of ClassificationResultConsumer."""
    return ClassificationResultConsumer.get_instance()
