from uuid import UUID

from pydantic import BaseModel


class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
