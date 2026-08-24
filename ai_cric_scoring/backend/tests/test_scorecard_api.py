from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.api_helpers import bearer, register_user
from tests.match_helpers import create_ready_match


def _start_body(fixture: dict) -> dict:
    batting = fixture["batting"]["players"]
    bowling = fixture["bowling"]["players"]
    return {
        "striker_id": batting[0]["id"],
        "non_striker_id": batting[1]["id"],
        "bowler_id": bowling[0]["id"],
        "client_event_id": str(uuid4()),
    }


def _delivery(revision: int, **fields: object) -> dict:
    delivery = {
        "runs_off_bat": 0,
        "wides": 0,
        "no_balls": 0,
        "byes": 0,
        "leg_byes": 0,
        "penalty_runs": 0,
        "dismissal": None,
        **fields,
    }
    return {
        "client_event_id": str(uuid4()),
        "base_revision": revision,
        "type": "DELIVERY",
        "delivery": delivery,
    }


async def _score(client: AsyncClient, match_id: str, headers: dict, revision: int, **fields: object) -> dict:
    response = await client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(revision, **fields),
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _scorecard(client: AsyncClient, match_id: str, headers: dict) -> dict:
    response = await client.get(f"/api/v1/matches/{match_id}/scorecard", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _assert_innings_invariants(innings: dict) -> None:
    batter_runs = sum(row["runs"] for row in innings["batting"])
    assert batter_runs + innings["extras"]["total"] == innings["runs"]
    extras = innings["extras"]
    assert (
        extras["total"]
        == extras["wides"] + extras["no_balls"] + extras["byes"] + extras["leg_byes"] + extras["penalty_runs"]
    )
    team_wickets = innings["wickets"]
    assert team_wickets == len(innings["fall_of_wickets"])
    bowler_wickets = sum(row["wickets"] for row in innings["bowling"])
    assert bowler_wickets <= team_wickets
    assert sum(row["legal_balls"] for row in innings["bowling"]) == innings["legal_balls"]
    bowler_runs = sum(row["runs_conceded"] for row in innings["bowling"])
    assert bowler_runs + extras["byes"] + extras["leg_byes"] + extras["penalty_runs"] == innings["runs"]


@pytest.mark.asyncio
async def test_ready_match_scorecard_is_empty(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    body = await _scorecard(auth_client, fixture["match"]["id"], fixture["headers"])
    assert body["status"] == "READY"
    assert body["innings"] == []
    assert body["match"]["team_a"]["name"] == "Alpha"


@pytest.mark.asyncio
async def test_live_scorecard_sequence_extras_wicket_and_undo(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    revision = start.json()["revision"]
    incoming = fixture["batting"]["players"][2]["id"]

    live = await _score(auth_client, match_id, headers, revision, runs_off_bat=1)
    live = await _score(auth_client, match_id, headers, live["revision"], runs_off_bat=4)
    live = await _score(auth_client, match_id, headers, live["revision"], wides=1)
    live = await _score(auth_client, match_id, headers, live["revision"], no_balls=1, runs_off_bat=2)
    dismissed_id = live["striker"]["match_player_id"]
    live = await _score(
        auth_client,
        match_id,
        headers,
        live["revision"],
        dismissal={"type": "BOWLED", "dismissed_player_id": dismissed_id},
    )
    selected = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/select-batter",
        json={"client_event_id": str(uuid4()), "base_revision": live["revision"], "player_id": incoming},
        headers=headers,
    )
    assert selected.status_code == 200, selected.text
    live = await _score(auth_client, match_id, headers, selected.json()["revision"])
    live = await _score(auth_client, match_id, headers, live["revision"], runs_off_bat=2)

    card = await _scorecard(auth_client, match_id, headers)
    innings = card["innings"][0]
    assert card["status"] == "LIVE"
    assert innings["runs"] == 11
    assert innings["wickets"] == 1
    assert innings["legal_balls"] == 5
    assert innings["overs"] == "0.5"
    assert innings["extras"] == {
        "total": 2,
        "wides": 1,
        "no_balls": 1,
        "byes": 0,
        "leg_byes": 0,
        "penalty_runs": 0,
    }
    _assert_innings_invariants(innings)
    dismissed = next(row for row in innings["batting"] if row["match_player_id"] == dismissed_id)
    assert dismissed["dismissal_text"].startswith("b ")
    not_out = [row for row in innings["batting"] if row["dismissal_text"] == "not out"]
    assert not_out
    assert innings["fall_of_wickets"][0]["wicket_number"] == 1
    assert innings["fall_of_wickets"][0]["score"] == 9
    assert any(row["is_current"] for row in innings["partnerships"])
    assert innings["overs_summary"][0]["deliveries"][2]["label"] == "WD"
    assert innings["overs_summary"][0]["deliveries"][3]["label"] == "2NB"
    four_row = next(row for row in innings["batting"] if row["fours"] == 1)
    assert four_row["runs"] >= 4

    before_undo = innings["runs"]
    undone = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/undo",
        json={"client_event_id": str(uuid4()), "base_revision": live["revision"]},
        headers=headers,
    )
    assert undone.status_code == 200, undone.text
    after = await _scorecard(auth_client, match_id, headers)
    assert after["innings"][0]["runs"] == before_undo - 2
    _assert_innings_invariants(after["innings"][0])


@pytest.mark.asyncio
async def test_byes_run_out_retired_hurt_and_security(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    revision = start.json()["revision"]
    non_striker = start.json()["non_striker"]["match_player_id"]
    fielder = fixture["bowling"]["players"][0]["id"]
    incoming = fixture["batting"]["players"][2]["id"]

    live = await _score(auth_client, match_id, headers, revision, byes=4)
    live = await _score(
        auth_client,
        match_id,
        headers,
        live["revision"],
        dismissal={
            "type": "RUN_OUT",
            "dismissed_player_id": non_striker,
            "fielder_id": fielder,
        },
    )
    await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/select-batter",
        json={"client_event_id": str(uuid4()), "base_revision": live["revision"], "player_id": incoming},
        headers=headers,
    )
    live = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json={
            "client_event_id": str(uuid4()),
            "base_revision": live["revision"] + 1,
            "type": "RETIRE",
            "retire": {"player_id": incoming, "hurt": True},
        },
        headers=headers,
    )
    assert live.status_code == 200, live.text

    card = await _scorecard(auth_client, match_id, headers)
    innings = card["innings"][0]
    assert innings["extras"]["byes"] == 4
    assert innings["wickets"] == 1
    run_out = next(row for row in innings["batting"] if row["match_player_id"] == non_striker)
    assert run_out["dismissal_text"].startswith("run out")
    assert innings["bowling"][0]["wickets"] == 0
    hurt = next(row for row in innings["batting"] if row["match_player_id"] == incoming)
    assert hurt["dismissal_text"] == "retired hurt"
    assert all(item["player_id"] != incoming for item in innings["fall_of_wickets"])
    _assert_innings_invariants(innings)

    forbidden = await auth_client.get(f"/api/v1/matches/{match_id}/scorecard", headers=bearer(other))
    assert forbidden.status_code == 404
    missing = await auth_client.get(f"/api/v1/matches/{uuid4()}/scorecard", headers=headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_completed_chase_custom_balls_and_all_out(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=1, balls=5, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    live = start.json()
    for _ in range(5):
        live = await _score(auth_client, match_id, headers, live["revision"], runs_off_bat=1)
    assert live["needs_openers"] is True
    between = await _scorecard(auth_client, match_id, headers)
    assert len(between["innings"]) == 1
    assert between["innings"][0]["overs"] == "1.0"
    assert between["innings"][0]["legal_balls"] == 5
    _assert_innings_invariants(between["innings"][0])

    pending = live["pending_innings_id"]
    second = await auth_client.post(
        f"/api/v1/matches/{match_id}/innings/{pending}/start",
        json={
            "striker_id": fixture["bowling"]["players"][0]["id"],
            "non_striker_id": fixture["bowling"]["players"][1]["id"],
            "bowler_id": fixture["batting"]["players"][0]["id"],
            "client_event_id": str(uuid4()),
        },
        headers=headers,
    )
    assert second.status_code == 200, second.text
    chase = await _score(auth_client, match_id, headers, second.json()["revision"], runs_off_bat=6)
    assert chase["status"] == "COMPLETED"
    completed = await _scorecard(auth_client, match_id, headers)
    assert completed["status"] == "COMPLETED"
    assert len(completed["innings"]) == 2
    assert completed["innings"][1]["target"] == 6
    assert completed["innings"][1]["required_run_rate"] == 0.0
    assert completed["match"]["result_type"] == "WON"
    assert completed["summary"]["total_boundaries"] >= 1
    _assert_innings_invariants(completed["innings"][0])
    _assert_innings_invariants(completed["innings"][1])

    tiny = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3, label="Gamma")
    tiny_id = tiny["match"]["id"]
    tiny_headers = tiny["headers"]
    started = await auth_client.post(f"/api/v1/matches/{tiny_id}/start", json=_start_body(tiny), headers=tiny_headers)
    live = started.json()
    first = live["striker"]["match_player_id"]
    last = tiny["batting"]["players"][2]["id"]
    live = await _score(
        auth_client,
        tiny_id,
        tiny_headers,
        live["revision"],
        dismissal={"type": "BOWLED", "dismissed_player_id": first},
    )
    selected = await auth_client.post(
        f"/api/v1/matches/{tiny_id}/scoring/select-batter",
        json={"client_event_id": str(uuid4()), "base_revision": live["revision"], "player_id": last},
        headers=tiny_headers,
    )
    assert selected.status_code == 200, selected.text
    current = selected.json()["striker"]["match_player_id"]
    await _score(
        auth_client,
        tiny_id,
        tiny_headers,
        selected.json()["revision"],
        dismissal={"type": "BOWLED", "dismissed_player_id": current},
    )
    all_out = await _scorecard(auth_client, tiny_id, tiny_headers)
    assert all_out["innings"][0]["all_out"] is True
    assert all_out["innings"][0]["wickets"] == 2
    _assert_innings_invariants(all_out["innings"][0])


@pytest.mark.asyncio
async def test_undo_wicket_removes_fow(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    striker = start.json()["striker"]["match_player_id"]
    live = await _score(
        auth_client,
        match_id,
        headers,
        start.json()["revision"],
        dismissal={"type": "BOWLED", "dismissed_player_id": striker},
    )
    with_wicket = await _scorecard(auth_client, match_id, headers)
    assert with_wicket["innings"][0]["wickets"] == 1
    assert with_wicket["innings"][0]["fall_of_wickets"]
    await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/undo",
        json={"client_event_id": str(uuid4()), "base_revision": live["revision"]},
        headers=headers,
    )
    restored = await _scorecard(auth_client, match_id, headers)
    innings = restored["innings"][0]
    assert innings["wickets"] == 0
    assert innings["fall_of_wickets"] == []
    batter = next(row for row in innings["batting"] if row["match_player_id"] == striker)
    assert batter["dismissal_text"] == "not out"
    _assert_innings_invariants(innings)
