import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user


async def _create_team(client: AsyncClient, account: dict, name: str, short_name: str | None = None) -> dict:
    payload: dict = {"name": name}
    if short_name is not None:
        payload["short_name"] = short_name
    response = await client.post("/api/v1/teams", json=payload, headers=bearer(account))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_team_access_denied(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/teams")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list_and_get_owned_team(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "owner@example.com")
    created = await _create_team(auth_client, account, "  Weekend Warriors  ", " ww ")
    assert created["name"] == "Weekend Warriors"
    assert created["short_name"] == "ww"
    assert created["is_active"] is True
    assert created["player_count"] == 0
    assert "owner_user_id" not in created

    listed = await auth_client.get("/api/v1/teams", headers=bearer(account))
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == created["id"]

    detail = await auth_client.get(f"/api/v1/teams/{created['id']}", headers=bearer(account))
    assert detail.status_code == 200
    assert detail.json()["name"] == "Weekend Warriors"


@pytest.mark.asyncio
async def test_duplicate_team_name_conflict(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "dup@example.com")
    await _create_team(auth_client, account, "Office XI")
    response = await auth_client.post(
        "/api/v1/teams",
        json={"name": "Office XI"},
        headers=bearer(account),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TEAM_NAME_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_update_team_and_inactive_filter(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "edit@example.com")
    team = await _create_team(auth_client, account, "Titans")
    updated = await auth_client.patch(
        f"/api/v1/teams/{team['id']}",
        json={"name": "City Titans", "is_active": False},
        headers=bearer(account),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "City Titans"
    assert updated.json()["is_active"] is False

    active = await auth_client.get("/api/v1/teams", params={"is_active": True}, headers=bearer(account))
    assert active.json()["total"] == 0
    inactive = await auth_client.get("/api/v1/teams", params={"is_active": False}, headers=bearer(account))
    assert inactive.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_teams(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "search@example.com")
    await _create_team(auth_client, account, "Weekend Warriors", "WW")
    await _create_team(auth_client, account, "Office XI", "OXI")
    response = await auth_client.get("/api/v1/teams", params={"search": "warriors"}, headers=bearer(account))
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Weekend Warriors"


@pytest.mark.asyncio
async def test_other_user_team_is_not_visible(auth_client: AsyncClient) -> None:
    user_a = await register_user(auth_client, "teama@example.com")
    user_b = await register_user(auth_client, "teamb@example.com")
    team = await _create_team(auth_client, user_a, "Secret XI")

    listed = await auth_client.get("/api/v1/teams", headers=bearer(user_b))
    assert listed.json()["total"] == 0

    detail = await auth_client.get(f"/api/v1/teams/{team['id']}", headers=bearer(user_b))
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "TEAM_NOT_FOUND"

    patched = await auth_client.patch(
        f"/api/v1/teams/{team['id']}",
        json={"name": "Hijacked"},
        headers=bearer(user_b),
    )
    assert patched.status_code == 404
