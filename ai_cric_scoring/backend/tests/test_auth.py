from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AccountInactiveError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService


@pytest.fixture
def auth_service(db_session: AsyncSession) -> AuthService:
    return AuthService(db_session, Settings())


@pytest.fixture
def token_service() -> TokenService:
    return TokenService(Settings())


async def _register(
    client: AsyncClient,
    email: str = "user@example.com",
    password: str = "strong-password",
    display_name: str = "Darshil",
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_register_creates_user_and_tokens(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    body = await _register(auth_client, email="Darshil@Example.com")
    assert body["user"]["email"] == "darshil@example.com"
    assert body["user"]["display_name"] == "Darshil"
    assert body["user"]["is_active"] is True
    assert "password_hash" not in body["user"]
    assert body["tokens"]["token_type"] == "bearer"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]

    user = await db_session.scalar(select(User).where(User.email == "darshil@example.com"))
    assert user is not None
    assert user.password_hash != "strong-password"
    assert PasswordService().verify_password("strong-password", user.password_hash)

    sessions = list((await db_session.execute(select(RefreshToken))).scalars())
    assert len(sessions) == 1
    assert sessions[0].token_hash != body["tokens"]["refresh_token"]
    assert len(sessions[0].token_hash) == 64


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    response = await auth_client.post(
        "/api/v1/auth/register",
        json={"email": "USER@example.com", "password": "another-password"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.asyncio
async def test_login_success_and_normalized_email(auth_client: AsyncClient) -> None:
    await _register(auth_client, email="owner@example.com")
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "Owner@Example.com", "password": "strong-password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "owner@example.com"
    assert body["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_and_unknown_email(auth_client: AsyncClient) -> None:
    await _register(auth_client)
    wrong = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "not-the-password"},
    )
    missing = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "strong-password"},
    )
    assert wrong.status_code == 401
    assert missing.status_code == 401
    assert wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert missing.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong.json()["error"]["message"] == missing.json()["error"]["message"]


@pytest.mark.asyncio
async def test_login_inactive_user_http(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    await _register(auth_client, email="idle@example.com")
    user = await db_session.scalar(select(User).where(User.email == "idle@example.com"))
    assert user is not None
    user.is_active = False
    await db_session.flush()
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "idle@example.com", "password": "strong-password"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_INACTIVE"


@pytest.mark.asyncio
async def test_register_rejects_short_password(auth_client: AsyncClient) -> None:
    response = await auth_client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_inactive_user(db_session: AsyncSession, auth_service: AuthService) -> None:
    result = await auth_service.register(
        email="idle@example.com",
        password="strong-password",
        display_name=None,
    )
    result.user.is_active = False
    await db_session.flush()
    with pytest.raises(AccountInactiveError):
        await auth_service.login(email="idle@example.com", password="strong-password")


@pytest.mark.asyncio
async def test_me_requires_valid_access_token(auth_client: AsyncClient) -> None:
    registered = await _register(auth_client)
    missing = await auth_client.get("/api/v1/auth/me")
    assert missing.status_code == 401

    malformed = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert malformed.status_code == 401
    assert malformed.json()["error"]["code"] == "INVALID_TOKEN"

    ok = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered['tokens']['access_token']}"},
    )
    assert ok.status_code == 200
    assert ok.json()["email"] == "user@example.com"
    assert "password_hash" not in ok.json()


@pytest.mark.asyncio
async def test_expired_and_wrong_type_access_token(
    auth_client: AsyncClient,
    token_service: TokenService,
    db_session: AsyncSession,
) -> None:
    registered = await _register(auth_client)
    user_id = registered["user"]["id"]
    expired = token_service.create_access_token(
        UUID(user_id),
        expires_delta=timedelta(seconds=-5),
    )
    expired_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert expired_response.status_code == 401
    assert expired_response.json()["error"]["code"] == "TOKEN_EXPIRED"

    settings = Settings()
    refresh_as_access = jwt.encode(
        {
            "sub": user_id,
            "type": "refresh",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    wrong_type = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_as_access}"},
    )
    assert wrong_type.status_code == 401
    assert wrong_type.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_inactive_user_cannot_use_access_token(
    auth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    registered = await _register(auth_client)
    user = await db_session.scalar(select(User).where(User.email == "user@example.com"))
    assert user is not None
    user.is_active = False
    await db_session.flush()
    response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered['tokens']['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_INACTIVE"


@pytest.mark.asyncio
async def test_refresh_rotates_and_old_token_fails(auth_client: AsyncClient) -> None:
    registered = await _register(auth_client)
    old_refresh = registered["tokens"]["refresh_token"]
    first = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200
    new_refresh = first.json()["tokens"]["refresh_token"]
    assert new_refresh != old_refresh

    reused = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "SESSION_REVOKED"

    second = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert second.status_code == 200
    me = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second.json()['tokens']['access_token']}"},
    )
    assert me.status_code == 200


@pytest.mark.asyncio
async def test_refresh_invalid_and_expired(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    token_service: TokenService,
) -> None:
    invalid = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "this-is-not-a-valid-refresh-token"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "INVALID_TOKEN"

    registered = await _register(auth_client, email="expiring@example.com")
    refresh = registered["tokens"]["refresh_token"]
    token_hash = token_service.hash_refresh_token(refresh)
    session = await db_session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    assert session is not None
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.flush()
    expired = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert expired.status_code == 401
    assert expired.json()["error"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_logout_revokes_refresh(auth_client: AsyncClient) -> None:
    registered = await _register(auth_client)
    refresh = registered["tokens"]["refresh_token"]
    logout = await auth_client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert logout.status_code == 204
    again = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert again.status_code == 401
    second_logout = await auth_client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert second_logout.status_code == 204


@pytest.mark.asyncio
async def test_password_service_hashes_with_argon2() -> None:
    service = PasswordService()
    hashed = service.hash_password("strong-password")
    assert hashed != "strong-password"
    assert hashed.startswith("$argon2")
    assert service.verify_password("strong-password", hashed)
    assert not service.verify_password("wrong", hashed)
