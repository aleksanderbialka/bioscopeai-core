from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
