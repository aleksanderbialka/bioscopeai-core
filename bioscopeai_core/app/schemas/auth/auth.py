import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints


class PasswordValidationError(ValueError):
    def __init__(self, reason: str) -> None:
        message = f"Password validation error: {reason}"
        super().__init__(message)


class RegisterIn(BaseModel):
    email: Annotated[EmailStr, Field(min_length=5, max_length=100)]
    first_name: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    last_name: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=50)]

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            msg = "must contain at least one uppercase letter"
            raise PasswordValidationError(msg)
        if not re.search(r"[a-z]", v):
            msg = "must contain at least one lowercase letter"
            raise PasswordValidationError(msg)
        if not re.search(r"\d", v):
            msg = "must contain at least one digit"
            raise PasswordValidationError(msg)
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            msg = "must contain at least one special character"
            raise PasswordValidationError(msg)
        return v


class LoginIn(BaseModel):
    email: Annotated[EmailStr, Field(min_length=5, max_length=100)]
    password: Annotated[str, Field(min_length=8, max_length=50)]


class TokenOut(BaseModel):
    access_token: str
    token_type: str
