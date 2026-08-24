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


@pytest.mark.asyncio
async def test_start_ready_match_and_score_delivery(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]

    started = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    assert started.status_code == 200, started.text
    body = started.json()
    assert body["status"] == "LIVE"
    assert body["revision"] == 1
    assert body["innings"]["runs"] == 0
    assert body["innings"]["balls_remaining"] == 12
    assert body["available_batters"]
    assert body["available_bowlers"]
    assert body["striker"]["match_player_id"] == fixture["batting"]["players"][0]["id"]

    scored = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(1, runs_off_bat=1),
        headers=headers,
    )
    assert scored.status_code == 200, scored.text
    assert scored.json()["innings"]["runs"] == 1
    assert scored.json()["innings"]["legal_balls"] == 1
    assert scored.json()["striker"]["match_player_id"] == fixture["batting"]["players"][1]["id"]

    extras = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(scored.json()["revision"], byes=2),
        headers=headers,
    )
    assert extras.status_code == 200, extras.text
    assert extras.json()["innings"]["runs"] == 3
    assert extras.json()["bowler"]["runs"] == 1


@pytest.mark.asyncio
async def test_start_non_ready_rejected(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    response = await auth_client.post(
        "/api/v1/matches",
        json={"format": "T20", "players_per_team": 2},
        headers=bearer(owner),
    )
    match_id = response.json()["id"]
    started = await auth_client.post(
        f"/api/v1/matches/{match_id}/start",
        json={
            "striker_id": str(uuid4()),
            "non_striker_id": str(uuid4()),
            "bowler_id": str(uuid4()),
            "client_event_id": str(uuid4()),
        },
        headers=bearer(owner),
    )
    assert started.status_code == 409
    assert started.json()["error"]["code"] == "MATCH_NOT_READY"


@pytest.mark.asyncio
async def test_other_user_cannot_score(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "owner@example.com")
    other = await register_user(auth_client, "other@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=1, balls=6, players=2)
    match_id = fixture["match"]["id"]
    await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=fixture["headers"])
    headers = bearer(other)
    for method, path, payload in (
        ("get", f"/api/v1/matches/{match_id}/live", None),
        ("post", f"/api/v1/matches/{match_id}/scoring/events", _delivery(1, runs_off_bat=1)),
        (
            "post",
            f"/api/v1/matches/{match_id}/scoring/select-batter",
            {"client_event_id": str(uuid4()), "base_revision": 1, "player_id": str(uuid4())},
        ),
        (
            "post",
            f"/api/v1/matches/{match_id}/scoring/select-bowler",
            {"client_event_id": str(uuid4()), "base_revision": 1, "player_id": str(uuid4())},
        ),
        (
            "post",
            f"/api/v1/matches/{match_id}/scoring/undo",
            {"client_event_id": str(uuid4()), "base_revision": 1},
        ),
        ("post", f"/api/v1/matches/{match_id}/start", _start_body(fixture)),
    ):
        if method == "get":
            response = await auth_client.get(path, headers=headers)
        else:
            response = await auth_client.post(path, json=payload, headers=headers)
        assert response.status_code == 404, path


@pytest.mark.asyncio
async def test_wicket_select_batter_over_and_bowler(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=3)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    revision = start.json()["revision"]
    striker = start.json()["striker"]["match_player_id"]
    incoming = fixture["batting"]["players"][2]["id"]
    next_bowler = fixture["bowling"]["players"][1]["id"]

    wicket = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(
            revision,
            dismissal={"type": "BOWLED", "dismissed_player_id": striker},
        ),
        headers=headers,
    )
    assert wicket.status_code == 200, wicket.text
    assert wicket.json()["needs_new_batter"] is True
    assert wicket.json()["innings"]["wickets"] == 1
    revision = wicket.json()["revision"]

    selected = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/select-batter",
        json={"client_event_id": str(uuid4()), "base_revision": revision, "player_id": incoming},
        headers=headers,
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["needs_new_batter"] is False
    revision = selected.json()["revision"]

    for _ in range(5):
        response = await auth_client.post(
            f"/api/v1/matches/{match_id}/scoring/events",
            json=_delivery(revision),
            headers=headers,
        )
        assert response.status_code == 200, response.text
        revision = response.json()["revision"]
    assert response.json()["needs_new_bowler"] is True

    bowler = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/select-bowler",
        json={"client_event_id": str(uuid4()), "base_revision": revision, "player_id": next_bowler},
        headers=headers,
    )
    assert bowler.status_code == 200, bowler.text
    assert bowler.json()["needs_new_bowler"] is False
    assert bowler.json()["bowler"]["match_player_id"] == next_bowler


@pytest.mark.asyncio
async def test_idempotency_and_revision_conflict(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=2, balls=6, players=2)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    payload = _delivery(start.json()["revision"], runs_off_bat=4)
    first = await auth_client.post(f"/api/v1/matches/{match_id}/scoring/events", json=payload, headers=headers)
    second = await auth_client.post(f"/api/v1/matches/{match_id}/scoring/events", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["idempotent"] is True
    assert first.json()["revision"] == second.json()["revision"]
    assert first.json()["innings"]["runs"] == 4

    stale = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(start.json()["revision"], runs_off_bat=1),
        headers=headers,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "SCORE_CONFLICT"
    assert stale.json()["error"]["current_revision"] == first.json()["revision"]


@pytest.mark.asyncio
async def test_extras_undo_and_tiny_chase(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "scorer@example.com")
    fixture = await create_ready_match(auth_client, owner, overs=1, balls=2, players=2)
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    start = await auth_client.post(f"/api/v1/matches/{match_id}/start", json=_start_body(fixture), headers=headers)
    revision = start.json()["revision"]

    wide = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(revision, wides=1),
        headers=headers,
    )
    assert wide.json()["innings"]["runs"] == 1
    assert wide.json()["innings"]["legal_balls"] == 0
    revision = wide.json()["revision"]

    undone = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/undo",
        json={"client_event_id": str(uuid4()), "base_revision": revision},
        headers=headers,
    )
    assert undone.status_code == 200, undone.text
    assert undone.json()["innings"]["runs"] == 0
    revision = undone.json()["revision"]

    four = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(revision, runs_off_bat=4),
        headers=headers,
    )
    assert four.json()["innings"]["runs"] == 4
    completed = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(four.json()["revision"]),
        headers=headers,
    )
    assert completed.json()["innings"]["status"] == "COMPLETED"
    assert completed.json()["needs_openers"] is True
    pending = completed.json()["pending_innings_id"]
    assert pending is not None
    assert completed.json()["chase_target"] == 5

    chase_start = {
        "striker_id": fixture["bowling"]["players"][0]["id"],
        "non_striker_id": fixture["bowling"]["players"][1]["id"],
        "bowler_id": fixture["batting"]["players"][0]["id"],
        "client_event_id": str(uuid4()),
    }
    second = await auth_client.post(
        f"/api/v1/matches/{match_id}/innings/{pending}/start",
        json=chase_start,
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["innings"]["number"] == 2
    assert second.json()["innings"]["target"] == 5

    winning = await auth_client.post(
        f"/api/v1/matches/{match_id}/scoring/events",
        json=_delivery(second.json()["revision"], runs_off_bat=6),
        headers=headers,
    )
    assert winning.status_code == 200, winning.text
    assert winning.json()["status"] == "COMPLETED"
    assert winning.json()["result_type"] == "WON"
    assert winning.json()["winner_match_team_id"] == fixture["bowling"]["id"]
    assert winning.json()["margin_wickets"] == 1
