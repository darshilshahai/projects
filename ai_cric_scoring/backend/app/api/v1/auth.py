from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.dependencies import client_user_agent, get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.user import UserPublic
from app.services.auth_service import AuthResult, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_response(result: AuthResult) -> AuthResponse:
    return AuthResponse(
        user=UserPublic.model_validate(result.user),
        tokens=TokenPair(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            token_type=result.tokens.token_type,
        ),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    result = await auth.register(
        email=str(payload.email),
        password=payload.password,
        display_name=payload.display_name,
        user_agent=client_user_agent(request),
    )
    return _to_response(result)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    result = await auth.login(
        email=str(payload.email),
        password=payload.password,
        user_agent=client_user_agent(request),
    )
    return _to_response(result)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    result = await auth.refresh(
        payload.refresh_token,
        user_agent=client_user_agent(request),
    )
    return _to_response(result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    await auth.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(user)
