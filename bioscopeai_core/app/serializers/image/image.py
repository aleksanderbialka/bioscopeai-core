from bioscopeai_core.app.models.image import Image
from bioscopeai_core.app.schemas.image import ImageMinimalOut, ImageOut


class ImageSerializer:
    @staticmethod
    def to_out(image: Image) -> ImageOut:
        return ImageOut(
            id=image.id,
            filename=image.filename,
            analyzed=image.analyzed,
            dataset_id=image.dataset_id,
            uploaded_by_id=image.uploaded_by_id,
            device_id=image.device_id or None,
            filepath=image.filepath,
            uploaded_at=image.uploaded_at,
        )

    def to_out_list(self, images: list[Image]) -> list[ImageOut]:
        return [self.to_out(img) for img in images]

    @staticmethod
    def to_minimal(image: Image) -> ImageMinimalOut:
        return ImageMinimalOut(
            id=image.id,
            filename=image.filename,
            analyzed=image.analyzed,
        )


def get_image_serializer() -> ImageSerializer:
    return ImageSerializer()
