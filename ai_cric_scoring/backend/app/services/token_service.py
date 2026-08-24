import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from app.core.config import Settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

TokenType = Literal["access"]


class TokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(
        self,
        user_id: uuid.UUID,
        *,
        expires_delta: timedelta | None = None,
    ) -> str:
        now = datetime.now(UTC)
        expires = now + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=self._settings.access_token_expire_minutes)
        )
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("The access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError("Invalid access token.") from exc

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid access token.")
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise InvalidTokenError("Invalid access token.")
        try:
            return uuid.UUID(subject)
        except ValueError as exc:
            raise InvalidTokenError("Invalid access token.") from exc

    def generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def refresh_expiry(self) -> datetime:
        return datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
