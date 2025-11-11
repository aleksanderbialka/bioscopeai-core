from typing import cast

from tortoise.models import Model


class BaseCRUD[T: Model]:
    model: type[T]

    async def get_all(self) -> list[T]:
        return cast("list[T]", await self.model.all())

    async def get_by_id(self, obj_id: str) -> T | None:
        return cast("T | None", await self.model.get_or_none(id=obj_id))

    async def delete_by_id(self, obj_id: str) -> bool:
        obj: T | None = await self.model.get_or_none(id=obj_id)
        if obj:
            await obj.delete()
            return True
        return False
