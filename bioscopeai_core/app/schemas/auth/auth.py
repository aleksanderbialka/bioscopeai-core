from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints


class RegisterIn(BaseModel):
    email: Annotated[EmailStr, Field(min_length=5, max_length=100)]
    first_name: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    last_name: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=50)]


class LoginIn(BaseModel):
    email: Annotated[EmailStr, Field(min_length=5, max_length=100)]
    password: Annotated[str, Field(min_length=8, max_length=50)]


class TokenOut(BaseModel):
    access_token: str
    token_type: str
