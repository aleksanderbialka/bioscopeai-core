from fastapi import APIRouter

from .health import health_router
from .routers import (
    auth_router,
    classification_result_router,
    classification_router,
    dataset_router,
    device_router,
    image_router,
    users_router,
)


api_router = APIRouter()


api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
api_router.include_router(dataset_router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(image_router, prefix="/images", tags=["Images"])
api_router.include_router(
    classification_router, prefix="/classifications", tags=["Classifications"]
)
api_router.include_router(
    classification_result_router,
    prefix="/classification-results",
    tags=["Classification Results"],
)
