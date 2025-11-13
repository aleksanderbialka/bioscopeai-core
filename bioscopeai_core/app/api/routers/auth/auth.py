from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from bioscopeai_core.app.auth import (
    obtain_token_pair,
    revoke_refresh,
    rotate_refresh_token,
    verify_login,
)
from bioscopeai_core.app.core.config import settings
from bioscopeai_core.app.models import User
from bioscopeai_core.app.schemas import LoginIn, RegisterIn, TokenOut


auth_router: APIRouter = APIRouter()


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(register_in: RegisterIn) -> dict[str, str]:
    if await User.filter(email=register_in.email).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already used"
        )
    if await User.filter(username=register_in.username).exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already used"
        )
    user = await User.create_user(
        email=register_in.email,
        username=register_in.username,
        first_name=register_in.first_name,
        last_name=register_in.last_name,
        password=register_in.password,
    )
    return {"id": str(user.id), "email": user.email}


@auth_router.post("/login", response_model=TokenOut)
async def login(login_in: LoginIn, response: Response) -> TokenOut:
    user = await verify_login(login_in.email, login_in.password)
    await user.update_last_login()
    access, refresh_raw = await obtain_token_pair(user=user)
    response.set_cookie(
        key="refresh_token",
        value=refresh_raw,
        httponly=True,
        secure=not settings.app.DEBUG,
        samesite="strict",
        max_age=settings.auth.REFRESH_TOKEN_TTL_MINUTES * 60,
    )
    return TokenOut(access_token=access, token_type="bearer")  # noqa: S106


@auth_router.post("/refresh", response_model=TokenOut)
async def refresh(request: Request, response: Response) -> TokenOut:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "Refresh token missing")
    access, new_refresh_raw = await rotate_refresh_token(refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_raw,
        httponly=True,
        secure=not settings.app.DEBUG,
        samesite="strict",
        max_age=settings.auth.REFRESH_TOKEN_TTL_MINUTES * 60,
    )
    return TokenOut(access_token=access, token_type="bearer")  # noqa: S106


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )
    await revoke_refresh(refresh_token)
    response.delete_cookie("refresh_token")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@auth_router.post("/login-swagger", response_model=TokenOut)
async def login_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> TokenOut:
    """
    Login endpoint for Swagger OAuth2 (uses form-data instead of JSON).
    """
    user = await verify_login(form_data.username, form_data.password)
    await user.update_last_login()
    access, refresh_raw = await obtain_token_pair(user=user)
    response.set_cookie(
        key="refresh_token",
        value=refresh_raw,
        httponly=True,
        secure=not settings.app.DEBUG,
        samesite="strict",
        max_age=settings.auth.REFRESH_TOKEN_TTL_MINUTES * 60,
    )
    return TokenOut(access_token=access, token_type="bearer")  # noqa: S106
