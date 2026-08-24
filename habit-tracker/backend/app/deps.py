from __future__ import annotations

from datetime import date, datetime, timezone
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.db.supabase import get_user_client
from supabase import Client

security = HTTPBearer(auto_error=False)

EDIT_WINDOW_DAYS = 7


class CurrentUser(BaseModel):
    id: UUID
    email: str | None = None
    access_token: str


@lru_cache
def _jwks_client(supabase_url: str, anon_key: str) -> PyJWKClient:
    """
    Supabase signing keys (ES256/RS256) are exposed at the Auth JWKS endpoint.
    Newer projects no longer use a shared HS256 JWT secret for access tokens.
    """
    url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(
        url,
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
        },
    )


def _decode_access_token(token: str, settings: Settings) -> dict:
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "HS256")

    # Legacy HS256 secret (older Supabase projects)
    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise jwt.InvalidTokenError("HS256 token but SUPABASE_JWT_SECRET is empty")
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )

    # Current Supabase default: asymmetric keys via JWKS (ES256 / RS256)
    jwks = _jwks_client(settings.supabase_url, settings.supabase_anon_key)
    signing_key = jwks.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = _decode_access_token(token, settings)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(
        id=UUID(sub),
        email=payload.get("email"),
        access_token=token,
    )


def get_db(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> Client:
    return get_user_client(user.access_token)


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def is_editable_date(entry_date: date, today: date | None = None) -> bool:
    """True for today and the previous EDIT_WINDOW_DAYS calendar days."""
    ref = today or today_utc()
    delta = (ref - entry_date).days
    return 0 <= delta <= EDIT_WINDOW_DAYS


def require_editable_date(entry_date: date) -> None:
    if not is_editable_date(entry_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Date {entry_date.isoformat()} is outside the edit window "
                f"(today + past {EDIT_WINDOW_DAYS} days)"
            ),
        )


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date: {value}. Use YYYY-MM-DD.",
        ) from exc
