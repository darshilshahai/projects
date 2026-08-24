from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user
from tests.match_helpers import create_draft, create_ready_match


def _start_body(fixture: dict) -> dict:
    batting = fixture["batting"]["players"]
    bowling = fixture["bowling"]["players"]
    return {
        "striker_id": batting[0]["id"],
        "non_striker_id": batting[1]["id"],
        "bowler_id": bowling[0]["id"],
        "client_event_id": str(uuid4()),
    }


async def _score(client: AsyncClient, match_id: str, headers: dict, revision: int, **fields: object) -> dict:
    response = await client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json={
            "client_event_id": str(uuid4()),
            "base_revision": revision,
            "type": "DELIVERY",
            "delivery": {
                "runs_off_bat": 0,
                "wides": 0,
                "no_balls": 0,
                "byes": 0,
                "leg_byes": 0,
                "penalty_runs": 0,
                "dismissal": None,
                **fields,
            },
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _complete(
    client: AsyncClient,
    account: dict,
    *,
    first_runs: int,
    second_runs: int,
    label: str,
    name: str | None = None,
    venue_name: str | None = None,
    match_format: str = "CUSTOM",
    players: int = 2,
) -> dict:
    fixture = await create_ready_match(
        client,
        account,
        format=match_format,
        overs=1,
        balls=1,
        players=players,
        label=label,
        name=name,
        venue_name=venue_name,
    )
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    live = (await client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)).json()
    live = await _score(client, match_id, headers, live["revision"], runs_off_bat=first_runs)
    second = await client.post(
        f"/api/v1/matches/{match_id}/innings/{live['pending_innings_id']}/start",
        json={
            "striker_id": fixture["bowling"]["players"][0]["id"],
            "non_striker_id": fixture["bowling"]["players"][1]["id"],
            "bowler_id": fixture["batting"]["players"][0]["id"],
            "client_event_id": str(uuid4()),
        },
        headers=headers,
    )
    assert second.status_code == 200, second.text
    live = await _score(client, match_id, headers, second.json()["revision"], runs_off_bat=second_runs)
    assert live["status"] == "COMPLETED"
    detail = await client.get(f"/api/v1/matches/{match_id}", headers=headers)
    assert detail.status_code == 200
    team_a = next(item for item in fixture["match"]["teams"] if item["side"] == "TEAM_A")
    return {
        "live": live,
        "detail": detail.json(),
        "fixture": fixture,
        "team_a_id": team_a["team_id"],
    }


@pytest.mark.asyncio
async def test_history_results_search_filters_and_isolation(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "historian@example.com")
    other = await register_user(auth_client, "visitor@example.com")
    await create_draft(auth_client, owner, name="Still Draft")
    runs = await _complete(
        auth_client,
        owner,
        first_runs=4,
        second_runs=1,
        label="Alpha",
        name="Sunday Final",
        venue_name="Central Ground",
    )
    wickets = await _complete(
        auth_client,
        owner,
        first_runs=1,
        second_runs=2,
        label="Beta",
        name="Office Cup",
        venue_name="Office Park",
    )
    tied = await _complete(
        auth_client,
        owner,
        first_runs=2,
        second_runs=2,
        label="Gamma",
        name="Weekend Practice",
    )

    runs_detail = runs["detail"]
    assert runs_detail["status"] == "COMPLETED"
    assert runs_detail["completed_at"] is not None
    assert runs_detail["result"]["result_type"] == "WON"
    assert runs_detail["result"]["margin_runs"] == 3
    assert runs_detail["result"]["margin_wickets"] is None
    assert runs_detail["result"]["winner_name"] == "Alpha"
    assert runs_detail["result"]["summary"] == "Alpha won by 3 runs"
    assert runs_detail["innings"][0]["runs"] == 4

    wickets_detail = wickets["detail"]
    assert wickets_detail["result"]["margin_wickets"] == 1
    assert wickets_detail["result"]["summary"] == "Beta Opp won by 1 wicket"

    assert tied["detail"]["result"]["result_type"] == "TIED"
    assert tied["detail"]["result"]["winner_match_team_id"] is None
    assert tied["detail"]["result"]["summary"] == "Match tied"

    history = await auth_client.get("/api/v1/matches?scope=history&limit=20", headers=bearer(owner))
    assert history.status_code == 200
    body = history.json()
    assert body["total"] == 3
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 3
    assert all(item["status"] == "COMPLETED" for item in body["items"])
    history_ids = {item["id"] for item in body["items"]}
    assert history_ids == {tied["detail"]["id"], wickets["detail"]["id"], runs["detail"]["id"]}
    completed_at = [item["completed_at"] for item in body["items"]]
    assert completed_at == sorted(completed_at, reverse=True)
    sunday = next(item for item in body["items"] if item["name"] == "Sunday Final")
    assert sunday["result"]["summary"] == "Alpha won by 3 runs"
    assert sunday["team_a_score"]["runs"] == 4

    page = await auth_client.get("/api/v1/matches?scope=history&limit=2&offset=0", headers=bearer(owner))
    next_page = await auth_client.get("/api/v1/matches?scope=history&limit=2&offset=2", headers=bearer(owner))
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 2
    assert len(next_page.json()["items"]) == 1
    ids = [item["id"] for item in page.json()["items"]] + [item["id"] for item in next_page.json()["items"]]
    assert len(ids) == len(set(ids))

    search = await auth_client.get("/api/v1/matches?scope=history&search=office", headers=bearer(owner))
    assert [item["name"] for item in search.json()["items"]] == ["Office Cup"]

    venue = await auth_client.get("/api/v1/matches?scope=history&search=Central", headers=bearer(owner))
    assert venue.json()["items"][0]["venue_name"] == "Central Ground"

    fmt = await auth_client.get("/api/v1/matches?scope=history&format=CUSTOM", headers=bearer(owner))
    assert fmt.json()["total"] == 3
    missing_format = await auth_client.get("/api/v1/matches?scope=history&format=T20", headers=bearer(owner))
    assert missing_format.json()["total"] == 0
    future = await auth_client.get(
        "/api/v1/matches?scope=history&date_from=2099-01-01T00:00:00Z",
        headers=bearer(owner),
    )
    assert future.json()["total"] == 0

    team = await auth_client.get(
        f"/api/v1/matches?scope=history&team_id={runs['team_a_id']}",
        headers=bearer(owner),
    )
    assert team.json()["total"] == 1
    assert team.json()["items"][0]["name"] == "Sunday Final"

    foreign_team = await auth_client.get(
        f"/api/v1/matches?scope=history&team_id={uuid4()}",
        headers=bearer(owner),
    )
    assert foreign_team.json()["total"] == 0

    invalid = await auth_client.get(
        "/api/v1/matches?scope=history&date_from=2026-08-15T00:00:00Z&date_to=2026-08-01T00:00:00Z",
        headers=bearer(owner),
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_DATE_RANGE"

    other_list = await auth_client.get("/api/v1/matches?scope=history", headers=bearer(other))
    assert other_list.json()["total"] == 0
    stolen = await auth_client.get(f"/api/v1/matches/{runs['detail']['id']}", headers=bearer(other))
    assert stolen.status_code == 404
    stolen_card = await auth_client.get(f"/api/v1/matches/{runs['detail']['id']}/scorecard", headers=bearer(other))
    assert stolen_card.status_code == 404

    active = await auth_client.get("/api/v1/matches?scope=active", headers=bearer(owner))
    assert active.json()["total"] == 1
    assert active.json()["items"][0]["name"] == "Still Draft"


@pytest.mark.asyncio
async def test_completed_match_is_immutable_and_keeps_snapshots(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "locked@example.com")
    completed = await _complete(
        auth_client,
        owner,
        first_runs=3,
        second_runs=0,
        label="Warriors",
        name="Snapshot Cup",
    )
    match_id = completed["detail"]["id"]
    headers = completed["fixture"]["headers"]
    team_id = completed["team_a_id"]

    patched = await auth_client.patch(f"/api/v1/matches/{match_id}", json={"name": "Hijack"}, headers=headers)
    assert patched.status_code == 409
    assert patched.json()["error"]["code"] == "MATCH_NOT_EDITABLE"

    teams = await auth_client.put(
        f"/api/v1/matches/{match_id}/teams",
        json={"team_a_id": team_id, "team_b_id": team_id},
        headers=headers,
    )
    assert teams.status_code == 409

    toss = await auth_client.put(
        f"/api/v1/matches/{match_id}/toss",
        json={"winner_match_team_id": completed["detail"]["teams"][0]["id"], "decision": "BAT"},
        headers=headers,
    )
    assert toss.status_code == 409

    scored = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json={
            "client_event_id": str(uuid4()),
            "base_revision": completed["live"]["revision"],
            "type": "DELIVERY",
            "delivery": {"runs_off_bat": 1, "wides": 0, "no_balls": 0, "byes": 0, "leg_byes": 0, "penalty_runs": 0},
        },
        headers=headers,
    )
    assert scored.status_code == 409
    assert scored.json()["error"]["code"] == "MATCH_COMPLETE"

    renamed = await auth_client.patch(f"/api/v1/teams/{team_id}", json={"name": "Warriors CC"}, headers=headers)
    assert renamed.status_code == 200
    history = await auth_client.get("/api/v1/matches?scope=history", headers=headers)
    assert history.json()["items"][0]["team_a_name"] == "Warriors"
    snapshot_search = await auth_client.get("/api/v1/matches?scope=history&search=Warriors", headers=headers)
    assert snapshot_search.json()["total"] == 1
    renamed_search = await auth_client.get("/api/v1/matches?scope=history&search=Warriors%20CC", headers=headers)
    assert renamed_search.json()["total"] == 0
    card = await auth_client.get(f"/api/v1/matches/{match_id}/scorecard", headers=headers)
    assert card.json()["match"]["team_a"]["name"] == "Warriors"
    player_id = completed["fixture"]["batting"]["players"][0]["player_id"]
    await auth_client.patch(f"/api/v1/players/{player_id}", json={"name": "Renamed Batter"}, headers=headers)
    card = await auth_client.get(f"/api/v1/matches/{match_id}/scorecard", headers=headers)
    names = [row["name"] for innings in card.json()["innings"] for row in innings["batting"]]
    assert "Renamed Batter" not in names
    assert any(name.startswith("Warriors") for name in names)


@pytest.mark.asyncio
async def test_small_team_chase_uses_maximum_wickets(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "smallteam@example.com")
    completed = await _complete(
        auth_client,
        owner,
        first_runs=1,
        second_runs=2,
        label="Five",
        players=5,
    )
    result = completed["detail"]["result"]
    assert result["result_type"] == "WON"
    assert result["margin_wickets"] == 4
    assert result["winner_name"] == "Five Opp"
    assert result["summary"] == "Five Opp won by 4 wickets"
