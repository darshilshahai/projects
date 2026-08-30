from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.auth import AuthResponse, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserLoginRequest, UserRegisterRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register new user account with unique email address.
    Returns created user profile and initial JWT Access & Refresh token pair.
    """
    service = AuthService(db)
    user, tokens = await service.register_user(data)
    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue tokens",
)
async def login(
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user credentials (email & password).
    Returns authenticated user profile and JWT Access & Refresh tokens.
    """
    service = AuthService(db)
    user, tokens = await service.authenticate_user(data)
    return AuthResponse(user=user, tokens=tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token with refresh token rotation",
)
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.
    Implements Refresh-Token Rotation: Revokes used refresh token and issues a new pair.
    """
    service = AuthService(db)
    tokens = await service.refresh_access_token(data.refresh_token)
    return tokens


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token and logout",
)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Revoke active refresh token on user logout."""
    service = AuthService(db)
    await service.logout_user(data.refresh_token)
    return {"message": "Successfully logged out."}
