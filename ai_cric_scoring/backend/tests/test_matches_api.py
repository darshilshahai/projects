from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user
from tests.match_helpers import create_draft, create_player, create_team, seed_squad, xi_payload


@pytest.mark.asyncio
async def test_unauthenticated_match_access_denied(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/matches")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_draft_assigns_owner_and_defaults(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "owner@example.com")
    created = await create_draft(auth_client, account, format="T20", name="Sunday League")
    assert created["status"] == "DRAFT"
    assert created["format"] == "T20"
    assert created["overs_per_innings"] == 20
    assert created["balls_per_over"] == 6
    assert created["players_per_team"] == 2
    assert created["name"] == "Sunday League"
    assert created["teams"] == []
    assert "created_by_user_id" not in created

    listed = await auth_client.get("/api/v1/matches", headers=bearer(account))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_invalid_overs_and_test_format_rejected(auth_client: AsyncClient) -> None:
    account = await register_user(auth_client, "owner@example.com")
    custom = await auth_client.post(
        "/api/v1/matches",
        json={"format": "CUSTOM"},
        headers=bearer(account),
    )
    assert custom.status_code == 400
    assert custom.json()["error"]["code"] == "INVALID_OVERS"

    test_format = await auth_client.post(
        "/api/v1/matches",
        json={"format": "TEST", "overs_per_innings": 20},
        headers=bearer(account),
    )
    assert test_format.status_code == 400
    assert test_format.json()["error"]["code"] == "INVALID_MATCH_FORMAT"


@pytest.mark.asyncio
async def test_other_user_cannot_access_match(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    created = await create_draft(auth_client, owner)

    response = await auth_client.get(f"/api/v1/matches/{created['id']}", headers=bearer(other))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MATCH_NOT_FOUND"

    patched = await auth_client.patch(
        f"/api/v1/matches/{created['id']}",
        json={"name": "Hijack"},
        headers=bearer(other),
    )
    assert patched.status_code == 404


@pytest.mark.asyncio
async def test_set_teams_validates_ownership_and_uniqueness(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    team_a, _ = await seed_squad(auth_client, owner, "Weekend Warriors", ["Rahul"])
    team_b, _ = await seed_squad(auth_client, owner, "Office XI", ["Arjun"])
    foreign, _ = await seed_squad(auth_client, other, "Invaders", ["Spy"])
    inactive = await create_team(auth_client, owner, "Old Boys")
    await auth_client.patch(
        f"/api/v1/teams/{inactive['id']}",
        json={"is_active": False},
        headers=bearer(owner),
    )
    match = await create_draft(auth_client, owner)

    same = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_a["id"], "team_b_id": team_a["id"]},
        headers=bearer(owner),
    )
    assert same.status_code == 409
    assert same.json()["error"]["code"] == "SAME_TEAM_SELECTED"

    stolen = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_a["id"], "team_b_id": foreign["id"]},
        headers=bearer(owner),
    )
    assert stolen.status_code == 404

    dead = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_a["id"], "team_b_id": inactive["id"]},
        headers=bearer(owner),
    )
    assert dead.status_code == 409
    assert dead.json()["error"]["code"] == "INACTIVE_TEAM"

    ok = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
        headers=bearer(owner),
    )
    assert ok.status_code == 200
    names = {item["side"]: item["name"] for item in ok.json()["teams"]}
    assert names["TEAM_A"] == "Weekend Warriors"
    assert names["TEAM_B"] == "Office XI"


@pytest.mark.asyncio
async def test_replacing_team_clears_that_side_xi(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    team_a, players_a = await seed_squad(auth_client, owner, "Warriors", ["Rahul", "Dev"])
    team_b, players_b = await seed_squad(auth_client, owner, "Office XI", ["Arjun", "Jay"])
    team_c, _ = await seed_squad(auth_client, owner, "Titans", ["Sam", "Ned"])
    match = await create_draft(auth_client, owner)
    teams = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
        headers=bearer(owner),
    )
    body = teams.json()
    side_a = next(item for item in body["teams"] if item["side"] == "TEAM_A")
    side_b = next(item for item in body["teams"] if item["side"] == "TEAM_B")
    await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], players_a), xi_payload(side_b["id"], players_b)]},
        headers=bearer(owner),
    )

    replaced = await auth_client.put(
        f"/api/v1/matches/{match['id']}/teams",
        json={"team_a_id": team_c["id"], "team_b_id": team_b["id"]},
        headers=bearer(owner),
    )
    assert replaced.status_code == 200
    new_a = next(item for item in replaced.json()["teams"] if item["side"] == "TEAM_A")
    new_b = next(item for item in replaced.json()["teams"] if item["side"] == "TEAM_B")
    assert new_a["name"] == "Titans"
    assert new_a["players"] == []
    assert len(new_b["players"]) == 2
    assert replaced.json()["toss"] is None


@pytest.mark.asyncio
async def test_playing_xi_validation(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    team_a, players_a = await seed_squad(auth_client, owner, "Warriors", ["Rahul", "Dev"])
    team_b, players_b = await seed_squad(auth_client, owner, "Office XI", ["Arjun", "Jay"])
    outsider = await create_player(auth_client, owner, "Not Rostered")
    foreign, foreign_players = await seed_squad(auth_client, other, "Invaders", ["Spy", "Mole"])
    match = await create_draft(auth_client, owner)
    teams = (
        await auth_client.put(
            f"/api/v1/matches/{match['id']}/teams",
            json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
            headers=bearer(owner),
        )
    ).json()
    side_a = next(item for item in teams["teams"] if item["side"] == "TEAM_A")
    side_b = next(item for item in teams["teams"] if item["side"] == "TEAM_B")

    not_rostered = await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], [players_a[0], outsider])]},
        headers=bearer(owner),
    )
    assert not_rostered.status_code == 409
    assert not_rostered.json()["error"]["code"] == "PLAYER_NOT_IN_ROSTER"

    duplicate = await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], [players_a[0], players_a[0]])]},
        headers=bearer(owner),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_PLAYING_XI_PLAYER"

    too_many = await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={
            "teams": [
                {
                    "match_team_id": side_a["id"],
                    "players": [
                        {"player_id": players_a[0]["id"]},
                        {"player_id": players_a[1]["id"]},
                        {"player_id": outsider["id"]},
                    ],
                }
            ]
        },
        headers=bearer(owner),
    )
    assert too_many.status_code == 409
    assert too_many.json()["error"]["code"] == "INVALID_PLAYING_XI_SIZE"

    await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], players_a)]},
        headers=bearer(owner),
    )
    cross = await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_b["id"], [players_a[0], players_b[0]])]},
        headers=bearer(owner),
    )
    assert cross.status_code == 409
    assert cross.json()["error"]["code"] == "DUPLICATE_PLAYING_XI_PLAYER"

    stolen = await auth_client.put(
        f"/api/v1/matches/{foreign['id'] if False else match['id']}/playing-xi",
        json={"teams": [xi_payload(side_b["id"], foreign_players)]},
        headers=bearer(owner),
    )
    assert stolen.status_code == 409


@pytest.mark.asyncio
async def test_toss_and_ready_lifecycle(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    team_a, players_a = await seed_squad(auth_client, owner, "Warriors", ["Rahul", "Dev"])
    team_b, players_b = await seed_squad(auth_client, owner, "Office XI", ["Arjun", "Jay"])
    match = await create_draft(auth_client, owner, venue_name="Central Ground")

    incomplete = await auth_client.post(f"/api/v1/matches/{match['id']}/ready", headers=bearer(owner))
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "MATCH_NOT_READY"
    assert "Select two teams." in incomplete.json()["error"]["details"]

    teams = (
        await auth_client.put(
            f"/api/v1/matches/{match['id']}/teams",
            json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
            headers=bearer(owner),
        )
    ).json()
    side_a = next(item for item in teams["teams"] if item["side"] == "TEAM_A")
    side_b = next(item for item in teams["teams"] if item["side"] == "TEAM_B")

    await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], players_a), xi_payload(side_b["id"], players_b)]},
        headers=bearer(owner),
    )

    foreign_toss = await auth_client.put(
        f"/api/v1/matches/{match['id']}/toss",
        json={"winner_match_team_id": str(uuid.uuid4()), "decision": "BAT"},
        headers=bearer(owner),
    )
    assert foreign_toss.status_code == 409
    assert foreign_toss.json()["error"]["code"] == "TOSS_TEAM_INVALID"

    toss = await auth_client.put(
        f"/api/v1/matches/{match['id']}/toss",
        json={"winner_match_team_id": side_a["id"], "decision": "BAT"},
        headers=bearer(owner),
    )
    assert toss.status_code == 200
    assert toss.json()["toss"]["decision"] == "BAT"

    ready = await auth_client.post(f"/api/v1/matches/{match['id']}/ready", headers=bearer(owner))
    assert ready.status_code == 200, ready.text
    assert ready.json()["status"] == "READY"
    assert ready.json()["readiness_issues"] == []
    assert ready.json()["teams"][0]["players"][0]["name"] == "Rahul"


@pytest.mark.asyncio
async def test_ready_requires_captain_keeper_and_equal_xi(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    team_a, players_a = await seed_squad(auth_client, owner, "Warriors", ["Rahul", "Dev"])
    team_b, players_b = await seed_squad(auth_client, owner, "Office XI", ["Arjun", "Jay"])
    match = await create_draft(auth_client, owner)
    teams = (
        await auth_client.put(
            f"/api/v1/matches/{match['id']}/teams",
            json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
            headers=bearer(owner),
        )
    ).json()
    side_a = next(item for item in teams["teams"] if item["side"] == "TEAM_A")
    side_b = next(item for item in teams["teams"] if item["side"] == "TEAM_B")
    await auth_client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={
            "teams": [
                {
                    "match_team_id": side_a["id"],
                    "players": [{"player_id": players_a[0]["id"], "is_captain": True}],
                },
                xi_payload(side_b["id"], players_b),
            ]
        },
        headers=bearer(owner),
    )
    await auth_client.put(
        f"/api/v1/matches/{match['id']}/toss",
        json={"winner_match_team_id": side_a["id"], "decision": "BOWL"},
        headers=bearer(owner),
    )
    ready = await auth_client.post(f"/api/v1/matches/{match['id']}/ready", headers=bearer(owner))
    assert ready.status_code == 409
    details = ready.json()["error"]["details"]
    assert any("Team A Playing XI requires 2 players." in item for item in details)


@pytest.mark.asyncio
async def test_other_user_cannot_configure_match(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    team_a, _ = await seed_squad(auth_client, owner, "Warriors", ["Rahul", "Dev"])
    team_b, _ = await seed_squad(auth_client, owner, "Office XI", ["Arjun", "Jay"])
    match = await create_draft(auth_client, owner)

    for method, path, payload in (
        ("put", f"/api/v1/matches/{match['id']}/teams", {"team_a_id": team_a["id"], "team_b_id": team_b["id"]}),
        (
            "put",
            f"/api/v1/matches/{match['id']}/playing-xi",
            {"teams": [{"match_team_id": str(uuid.uuid4()), "players": []}]},
        ),
        ("put", f"/api/v1/matches/{match['id']}/toss", {"winner_match_team_id": str(uuid.uuid4()), "decision": "BAT"}),
        ("post", f"/api/v1/matches/{match['id']}/ready", None),
    ):
        if method == "put":
            response = await auth_client.put(path, json=payload, headers=bearer(other))
        else:
            response = await auth_client.post(path, headers=bearer(other))
        assert response.status_code == 404, path
