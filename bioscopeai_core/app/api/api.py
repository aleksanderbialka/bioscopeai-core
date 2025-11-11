from fastapi import APIRouter

from .health import health_router
from .routers import auth_router, device_router, users_router


api_router = APIRouter()


api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
