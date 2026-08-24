import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user


async def _create_team(client: AsyncClient, account: dict, name: str) -> dict:
    response = await client.post("/api/v1/teams", json={"name": name}, headers=bearer(account))
    assert response.status_code == 201, response.text
    return response.json()


async def _create_player(client: AsyncClient, account: dict, name: str) -> dict:
    response = await client.post(
        "/api/v1/players",
        json={"name": name, "player_role": "BATTER", "batting_style": "RIGHT_HANDED"},
        headers=bearer(account),
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_add_list_remove_and_reactivate_roster(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "roster@example.com")
    team = await _create_team(auth_client, account, "Weekend Warriors")
    rahul = await _create_player(auth_client, account, "Rahul Shah")
    arjun = await _create_player(auth_client, account, "Arjun Mehta")

    added = await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": rahul["id"]},
        headers=bearer(account),
    )
    assert added.status_code == 201
    assert added.json()["name"] == "Rahul Shah"

    await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": arjun["id"]},
        headers=bearer(account),
    )
    roster = await auth_client.get(f"/api/v1/teams/{team['id']}/players", headers=bearer(account))
    assert roster.json()["total"] == 2

    duplicate = await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": rahul["id"]},
        headers=bearer(account),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PLAYER_ALREADY_IN_TEAM"

    removed = await auth_client.delete(
        f"/api/v1/teams/{team['id']}/players/{rahul['id']}",
        headers=bearer(account),
    )
    assert removed.status_code == 204
    after_remove = await auth_client.get(f"/api/v1/teams/{team['id']}/players", headers=bearer(account))
    assert after_remove.json()["total"] == 1
    assert after_remove.json()["items"][0]["name"] == "Arjun Mehta"

    readded = await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": rahul["id"]},
        headers=bearer(account),
    )
    assert readded.status_code == 201
    restored = await auth_client.get(f"/api/v1/teams/{team['id']}/players", headers=bearer(account))
    assert restored.json()["total"] == 2

    detail = await auth_client.get(f"/api/v1/teams/{team['id']}", headers=bearer(account))
    assert detail.json()["player_count"] == 2

    player = await auth_client.get(f"/api/v1/players/{rahul['id']}", headers=bearer(account))
    assert player.json()["teams"][0]["name"] == "Weekend Warriors"


@pytest.mark.asyncio
async def test_cannot_add_other_users_player_or_modify_other_team(auth_client: AsyncClient) -> None:
    user_a = await register_user(auth_client, "ownera@example.com")
    user_b = await register_user(auth_client, "ownerb@example.com")
    team_a = await _create_team(auth_client, user_a, "Team A")
    player_b = await _create_player(auth_client, user_b, "Player B")
    team_b = await _create_team(auth_client, user_b, "Team B")
    player_a = await _create_player(auth_client, user_a, "Player A")

    cross = await auth_client.post(
        f"/api/v1/teams/{team_a['id']}/players",
        json={"player_id": player_b["id"]},
        headers=bearer(user_a),
    )
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "PLAYER_NOT_FOUND"

    foreign_team = await auth_client.post(
        f"/api/v1/teams/{team_a['id']}/players",
        json={"player_id": player_b["id"]},
        headers=bearer(user_b),
    )
    assert foreign_team.status_code == 404
    assert foreign_team.json()["error"]["code"] == "TEAM_NOT_FOUND"

    await auth_client.post(
        f"/api/v1/teams/{team_a['id']}/players",
        json={"player_id": player_a["id"]},
        headers=bearer(user_a),
    )
    remove = await auth_client.delete(
        f"/api/v1/teams/{team_a['id']}/players/{player_a['id']}",
        headers=bearer(user_b),
    )
    assert remove.status_code == 404
    _ = team_b


@pytest.mark.asyncio
async def test_inactive_player_and_team_cannot_join_roster(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "inactive@example.com")
    team = await _create_team(auth_client, account, "Active XI")
    player = await _create_player(auth_client, account, "Idle Bat")
    await auth_client.patch(
        f"/api/v1/players/{player['id']}",
        json={"is_active": False},
        headers=bearer(account),
    )
    inactive_player = await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": player["id"]},
        headers=bearer(account),
    )
    assert inactive_player.status_code == 409
    assert inactive_player.json()["error"]["code"] == "INACTIVE_PLAYER"

    await auth_client.patch(
        f"/api/v1/players/{player['id']}",
        json={"is_active": True},
        headers=bearer(account),
    )
    await auth_client.patch(
        f"/api/v1/teams/{team['id']}",
        json={"is_active": False},
        headers=bearer(account),
    )
    inactive_team = await auth_client.post(
        f"/api/v1/teams/{team['id']}/players",
        json={"player_id": player["id"]},
        headers=bearer(account),
    )
    assert inactive_team.status_code == 409
    assert inactive_team.json()["error"]["code"] == "INACTIVE_TEAM"
