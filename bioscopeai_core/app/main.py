from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Lifespan

from bioscopeai_core.app.api import api_router
from bioscopeai_core.app.core.config import settings


def create_app(lifespan: Lifespan) -> FastAPI:
    app = FastAPI(
        debug=settings.app.DEBUG,
        title=settings.app.PROJECT_NAME,
        version=settings.app.PROJECT_VERSION,
        lifespan=lifespan,
    )

    if settings.app.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.app.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix="/api")
    return app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for startup and shutdown events."""
    yield


app: FastAPI = create_app(lifespan=lifespan)


def start_app() -> None:
    uvicorn.run(
        app=app,
        host=settings.app.UVICORN_ADDRESS,
        port=settings.app.UVICORN_PORT,
        log_level=settings.app.LOG_LEVEL,
        access_log=True,
    )


if __name__ == "__main__":
    start_app()
