from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    AccountInactiveError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    SessionRevokedError,
    TokenExpiredError,
)
from app.core.logging import get_logger
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.services.password_service import PasswordService
from app.services.persistence import flush_or_raise_conflict
from app.services.token_service import TokenService
from app.services.user import UserService

logger = get_logger(__name__)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def normalize_email(email: str) -> str:
    return email.strip().lower()


class IssuedTokens:
    def __init__(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = "bearer"


class AuthResult:
    def __init__(self, user: User, tokens: IssuedTokens) -> None:
        self.user = user
        self.tokens = tokens


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._user_service = UserService(session)
        self._refresh_tokens = RefreshTokenRepository(session)
        self._passwords = PasswordService()
        self._tokens = TokenService(settings)

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None,
        user_agent: str | None = None,
    ) -> AuthResult:
        normalized = normalize_email(email)
        existing = await self._users.get_by_email(normalized)
        if existing is not None:
            raise EmailAlreadyRegisteredError()

        user = await self._user_service.create(
            email=normalized,
            password_hash=self._passwords.hash_password(password),
            display_name=display_name.strip() if display_name else None,
        )
        tokens = await self._issue_session(user, user_agent=user_agent)
        logger.info("auth_register", user_id=str(user.id), status="success")
        return AuthResult(user=user, tokens=tokens)

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
    ) -> AuthResult:
        normalized = normalize_email(email)
        user = await self._users.get_by_email(normalized)
        if user is None or not self._passwords.verify_password(password, user.password_hash):
            logger.info("auth_login", status="invalid_credentials")
            raise InvalidCredentialsError()
        if not user.is_active:
            logger.info("auth_login", user_id=str(user.id), status="inactive")
            raise AccountInactiveError()
        tokens = await self._issue_session(user, user_agent=user_agent)
        logger.info("auth_login", user_id=str(user.id), status="success")
        return AuthResult(user=user, tokens=tokens)

    async def refresh(self, refresh_token: str, *, user_agent: str | None = None) -> AuthResult:
        session = await self._require_active_session(refresh_token)
        user = await self._user_service.get_by_id(session.user_id)
        if not user.is_active:
            session.revoked_at = datetime.now(UTC)
            await self._session.flush()
            raise AccountInactiveError()

        now = datetime.now(UTC)
        session.revoked_at = now
        session.last_used_at = now
        tokens = await self._issue_session(user, user_agent=user_agent or session.user_agent)
        logger.info("auth_refresh", user_id=str(user.id), status="success")
        return AuthResult(user=user, tokens=tokens)

    async def logout(self, refresh_token: str) -> None:
        token_hash = self._tokens.hash_refresh_token(refresh_token)
        session = await self._refresh_tokens.get_by_hash(token_hash)
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            await self._session.flush()
            logger.info("auth_logout", user_id=str(session.user_id), status="success")
        else:
            logger.info("auth_logout", status="already_revoked")

    async def get_current_user(self, access_token: str) -> User:
        user_id = self._tokens.decode_access_token(access_token)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("Invalid access token.")
        if not user.is_active:
            raise AccountInactiveError()
        return user

    async def _issue_session(self, user: User, *, user_agent: str | None) -> IssuedTokens:
        raw_refresh = self._tokens.generate_refresh_token()
        self._refresh_tokens.create(
            user_id=user.id,
            token_hash=self._tokens.hash_refresh_token(raw_refresh),
            expires_at=self._tokens.refresh_expiry(),
            user_agent=user_agent,
        )
        await flush_or_raise_conflict(self._session, "Could not create a session.")
        return IssuedTokens(
            access_token=self._tokens.create_access_token(user.id),
            refresh_token=raw_refresh,
        )

    async def _require_active_session(self, refresh_token: str) -> RefreshToken:
        token_hash = self._tokens.hash_refresh_token(refresh_token)
        session = await self._refresh_tokens.get_by_hash(token_hash)
        if session is None:
            raise InvalidTokenError("Invalid refresh token.")
        if session.revoked_at is not None:
            raise SessionRevokedError()
        if session.expires_at <= datetime.now(UTC):
            raise TokenExpiredError("The refresh token has expired.")
        return session
