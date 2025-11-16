from .auth import auth_router
from .classification import classification_result_router, classification_router
from .dataset import dataset_router
from .device import device_router
from .image import image_router
from .users import users_router


__all__ = [
    "auth_router",
    "classification_result_router",
    "classification_router",
    "dataset_router",
    "device_router",
    "image_router",
    "users_router",
]
