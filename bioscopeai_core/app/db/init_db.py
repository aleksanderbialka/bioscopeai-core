from typing import Any

from loguru import logger
from tortoise import Tortoise

from bioscopeai_core.app.core.config import settings


TORTOISE_ORM: dict[str, Any] = {
    "connections": {"default": settings.database.url},
    "apps": {
        "models": {
            "models": ["bioscopeai_core.app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


async def init_db() -> None:
    """Initialize the Tortoise ORM with the given configuration."""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        logger.info("Database initialized")
    except ConnectionError:
        logger.exception("Database connection error")
        raise
    except Exception:
        logger.exception("Unexpected error during database initialization")
        raise


async def close_db() -> None:
    """Close all database connections."""
    try:
        await Tortoise.close_connections()
        logger.info("Database connections closed")
    except Exception:  # noqa: BLE001
        logger.exception("Error closing database connections")
