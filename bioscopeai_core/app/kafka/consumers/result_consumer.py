from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from .base_consumer import BaseKafkaConsumer


class ClassificationResultConsumer(BaseKafkaConsumer):
    """Kafka consumer for classification results."""

    async def consume_messages(self) -> AsyncGenerator[Any]:
        """Consume messages from the Kafka topic."""
        if self._consumer:
            try:
                async for msg in self._consumer:
                    if self.should_stop_processing:
                        break
                    classification_result = msg.value.decode("utf-8")
                    logger.debug(
                        f"Consumed message from topic {msg.topic},"
                        f" partition {msg.partition},"
                        f" offset {msg.offset}: {classification_result}"
                    )
                    yield classification_result

            except Exception:
                logger.exception("Error while consuming messages")
                raise

    def _get_topic_name(self) -> str:
        return self.kafka_settings.CLASSIFICATION_RESULTS_TOPIC

    def _get_group_id(self) -> str:
        return self.kafka_settings.CLASSIFICATION_CONSUMER_GROUP
