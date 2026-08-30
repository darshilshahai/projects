import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_auth_lifecycle(async_client: AsyncClient):
    email = f"auth_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # 1. Register User
    register_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Auth Tester"},
    )
    assert register_res.status_code == 201
    reg_data = register_res.json()
    assert reg_data["user"]["email"] == email
    assert "access_token" in reg_data["tokens"]
    assert "refresh_token" in reg_data["tokens"]

    access_token = reg_data["tokens"]["access_token"]
    refresh_token = reg_data["tokens"]["refresh_token"]

    # 2. Duplicate Registration fails with 409 Conflict
    dup_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    # 3. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data["tokens"]

    # 4. Invalid Login
    bad_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword"},
    )
    assert bad_login.status_code == 401
    assert bad_login.json()["error"]["code"] == "INVALID_CREDENTIALS"

    # 5. Access Protected Endpoint (/users/me)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 6. Unauthenticated Access fails
    unauth_res = await async_client.get("/api/v1/users/me")
    assert unauth_res.status_code == 401

    # 7. Refresh Token Rotation
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token

    # 8. Reuse of old refresh token fails (Revoked token)
    old_refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert old_refresh_res.status_code == 401

    # 9. Logout
    new_refresh_token = new_tokens["refresh_token"]
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh_token},
    )
    assert logout_res.status_code == 200

    # 10. Using logged-out refresh token fails
    post_logout_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh_token},
    )
    assert post_logout_res.status_code == 401
