from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    RevokedTokenException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserLoginRequest, UserRegisterRequest


class AuthService:
    """Service Layer handling authentication logic and JWT lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, data: UserRegisterRequest) -> Tuple[User, TokenResponse]:
        """Register new user account and issue JWT tokens."""
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise EmailAlreadyExistsException()

        hashed_pwd = get_password_hash(data.password)
        user = await self.user_repo.create_user(
            email=data.email,
            hashed_password=hashed_pwd,
            full_name=data.full_name,
        )

        tokens = await self._generate_and_store_tokens(user.id)
        return user, tokens

    async def authenticate_user(self, data: UserLoginRequest) -> Tuple[User, TokenResponse]:
        """Authenticate email/password credentials and issue JWT tokens."""
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        tokens = await self._generate_and_store_tokens(user.id)
        return user, tokens

    async def refresh_access_token(self, raw_refresh_token: str) -> TokenResponse:
        """
        Refresh Access Token with Refresh-Token Rotation.
        Validates token, revokes used refresh token, and issues a new pair.
        """
        try:
            payload = decode_token(raw_refresh_token)
        except Exception:
            raise InvalidTokenException()

        if payload.get("type") != "refresh":
            raise InvalidTokenException("Token is not a valid refresh token.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenException()

        user_id = UUID(user_id_str)
        token_hash_str = hash_token(raw_refresh_token)
        token_record = await self.user_repo.get_refresh_token_by_hash(token_hash_str)

        if not token_record:
            raise InvalidTokenException("Refresh token unrecognized.")

        if token_record.is_revoked:
            raise RevokedTokenException()

        if token_record.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenException("Refresh token has expired.")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InactiveUserException()

        # Refresh Token Rotation: Revoke old token and issue new token pair
        await self.user_repo.revoke_refresh_token(token_hash_str)
        new_tokens = await self._generate_and_store_tokens(user.id)
        return new_tokens

    async def logout_user(self, raw_refresh_token: str) -> bool:
        """Revoke active refresh token on user logout."""
        token_hash_str = hash_token(raw_refresh_token)
        return await self.user_repo.revoke_refresh_token(token_hash_str)

    async def _generate_and_store_tokens(self, user_id: UUID) -> TokenResponse:
        """Internal helper to generate access/refresh tokens and store hashed refresh token."""
        access_token = create_access_token(user_id)
        raw_refresh_token, expires_at = create_refresh_token(user_id)
        token_hash_str = hash_token(raw_refresh_token)

        await self.user_repo.create_refresh_token(
            user_id=user_id,
            token_hash=token_hash_str,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
