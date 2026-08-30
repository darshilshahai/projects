import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_profile_management_lifecycle(async_client: AsyncClient):
    # 1. Register User
    email = f"profile_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OriginalPassword123!", "full_name": "Original Name"},
    )
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Profile
    me_res = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["email"] == email
    assert profile["full_name"] == "Original Name"

    # 3. Update Profile Name
    patch_res = await async_client.patch(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "Updated Name"

    # 4. Change Password - Invalid Current Password (returns 401 Invalid Credentials)
    bad_change = await async_client.post(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewSecretPassword123!",
        },
        headers=headers,
    )
    assert bad_change.status_code == 401

    # 5. Change Password - Success
    good_change = await async_client.post(
        "/api/v1/users/me/change-password",
        json={
            "current_password": "OriginalPassword123!",
            "new_password": "NewSecretPassword123!",
        },
        headers=headers,
    )
    assert good_change.status_code == 200

    # 6. Verify Login with New Password
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "NewSecretPassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()["tokens"]
