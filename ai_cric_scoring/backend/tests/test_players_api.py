import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user


async def _create_player(
    client: AsyncClient,
    account: dict,
    name: str,
    role: str = "BATTER",
) -> dict:
    response = await client.post(
        "/api/v1/players",
        json={
            "name": name,
            "player_role": role,
            "batting_style": "RIGHT_HANDED",
            "bowling_style": "UNKNOWN",
        },
        headers=bearer(account),
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_player_access_denied(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/players")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list_and_get_owned_player(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "players@example.com")
    created = await _create_player(auth_client, account, "  Rahul Shah  ")
    assert created["name"] == "Rahul Shah"
    assert created["player_role"] == "BATTER"
    assert created["is_active"] is True
    assert created["teams"] == []
    assert "owner_user_id" not in created

    listed = await auth_client.get("/api/v1/players", headers=bearer(account))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    detail = await auth_client.get(f"/api/v1/players/{created['id']}", headers=bearer(account))
    assert detail.status_code == 200
    assert detail.json()["name"] == "Rahul Shah"


@pytest.mark.asyncio
async def test_duplicate_player_names_allowed(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "twins@example.com")
    first = await _create_player(auth_client, account, "Rahul Patel")
    second = await _create_player(auth_client, account, "Rahul Patel", role="BOWLER")
    assert first["id"] != second["id"]
    listed = await auth_client.get("/api/v1/players", headers=bearer(account))
    assert listed.json()["total"] == 2


@pytest.mark.asyncio
async def test_player_enum_validation_and_role_filter(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "roles@example.com")
    invalid = await auth_client.post(
        "/api/v1/players",
        json={"name": "Bad Role", "player_role": "OPENER"},
        headers=bearer(account),
    )
    assert invalid.status_code == 422

    await _create_player(auth_client, account, "Arjun Mehta", role="ALL_ROUNDER")
    await _create_player(auth_client, account, "Neha Rao", role="BOWLER")
    filtered = await auth_client.get(
        "/api/v1/players",
        params={"role": "BOWLER"},
        headers=bearer(account),
    )
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["name"] == "Neha Rao"


@pytest.mark.asyncio
async def test_update_player_and_inactive_filter(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "editplayer@example.com")
    player = await _create_player(auth_client, account, "Karan")
    updated = await auth_client.patch(
        f"/api/v1/players/{player['id']}",
        json={"name": "Karan Shah", "player_role": "WICKET_KEEPER", "is_active": False},
        headers=bearer(account),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Karan Shah"
    assert updated.json()["player_role"] == "WICKET_KEEPER"
    assert updated.json()["is_active"] is False

    active = await auth_client.get("/api/v1/players", params={"is_active": True}, headers=bearer(account))
    assert active.json()["total"] == 0


@pytest.mark.asyncio
async def test_other_user_player_is_not_visible(auth_client: AsyncClient) -> None:
    user_a = await register_user(auth_client, "playa@example.com")
    user_b = await register_user(auth_client, "playb@example.com")
    player = await _create_player(auth_client, user_a, "Private Player")

    listed = await auth_client.get("/api/v1/players", headers=bearer(user_b))
    assert listed.json()["total"] == 0

    detail = await auth_client.get(f"/api/v1/players/{player['id']}", headers=bearer(user_b))
    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "PLAYER_NOT_FOUND"

    patched = await auth_client.patch(
        f"/api/v1/players/{player['id']}",
        json={"name": "Stolen"},
        headers=bearer(user_b),
    )
    assert patched.status_code == 404
