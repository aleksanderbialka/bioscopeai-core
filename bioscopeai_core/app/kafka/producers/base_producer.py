import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from loguru import logger

from bioscopeai_core.app.core.config import KafkaSettings, settings


class BaseKafkaProducer(ABC):
    """Abstract base class for Kafka producers."""

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self.kafka_settings: KafkaSettings = settings.kafka

    async def initialize(self) -> None:
        if self._producer is None:
            self._producer = self._create_base_producer()
        # Retry logic for starting the producer, in case of connection issues
        # Kafka may not be available immediately
        for attempt in range(1, 6):
            try:
                await self._producer.start()
            except KafkaConnectionError:
                logger.exception(f"Attempt {attempt} to start producer failed")
                await asyncio.sleep(2)
            else:
                logger.info("Kafka producer started successfully")
                return
        msg = "Failed to start Kafka producer after multiple attempts."
        logger.error(msg)
        raise RuntimeError(msg)

    @abstractmethod
    async def send_event(self, device_id: str, message: dict[str, Any]) -> None:
        """Send a message to the specified Kafka topic."""

    async def shutdown(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None

    def _create_base_producer(self) -> AIOKafkaProducer:
        return AIOKafkaProducer(
            bootstrap_servers=self.kafka_settings.BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
