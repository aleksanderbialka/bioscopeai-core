import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from loguru import logger

from bioscopeai_core.app.core.config import KafkaSettings, settings


class BaseKafkaConsumer(ABC):
    """Abstract base class for Kafka consumers."""

    def __init__(
        self,
    ) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self.kafka_settings: KafkaSettings = settings.kafka
        self.should_stop_processing: bool = False
        self.auto_commit_interval_ms: int = 60 * 1000
        self.enable_auto_commit: bool = False

    async def initialize(self) -> None:
        if self._consumer is None:
            self._consumer = self._create_base_consumer()
        # Retry logic for starting the consumer, in case of connection issues
        # Kafka may not be available immediately
        for attempt in range(1, 6):
            try:
                await self._consumer.start()
            except KafkaConnectionError:
                logger.exception(f"Attempt {attempt} to start consumer failed")
                await asyncio.sleep(2)
            else:
                logger.info("Kafka consumer started successfully")
                return
        msg = "Failed to start Kafka consumer after multiple attempts."
        logger.error(msg)
        raise RuntimeError(msg)

    @abstractmethod
    def consume_messages(self) -> AsyncGenerator[Any]:
        """Consume messages from the Kafka topic."""

    async def shutdown(self) -> None:
        """Shutdown connection if necessary"""
        self.should_stop_processing = True
        await asyncio.sleep(1)
        if self._consumer:
            await self._consumer.stop()

    async def commit_message(self) -> None:
        """Commit the current message offset."""
        if self._consumer:
            await self._consumer.commit()

    @abstractmethod
    def _get_topic_name(self) -> str:
        """Get the Kafka topic name to subscribe to."""

    @abstractmethod
    def _get_group_id(self) -> str:
        """Get the Kafka consumer group ID."""

    def _create_base_consumer(self) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            self._get_topic_name(),
            bootstrap_servers=self.kafka_settings.BOOTSTRAP_SERVERS,
            group_id=self._get_group_id(),
            enable_auto_commit=self.enable_auto_commit,
            auto_commit_interval_ms=self.auto_commit_interval_ms,
        )
