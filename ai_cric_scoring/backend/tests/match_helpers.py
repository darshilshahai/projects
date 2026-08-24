from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient

from tests.api_helpers import bearer


async def create_team(client: AsyncClient, account: dict, name: str) -> dict:
    response = await client.post("/api/v1/teams", json={"name": name, "short_name": name[:3]}, headers=bearer(account))
    assert response.status_code == 201, response.text
    return response.json()


async def create_player(client: AsyncClient, account: dict, name: str, role: str = "BATTER") -> dict:
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


async def add_to_roster(client: AsyncClient, account: dict, team_id: str, player_id: str) -> None:
    response = await client.post(
        f"/api/v1/teams/{team_id}/players",
        json={"player_id": player_id},
        headers=bearer(account),
    )
    assert response.status_code == 201, response.text


async def seed_squad(
    client: AsyncClient,
    account: dict,
    team_name: str,
    player_names: list[str],
) -> tuple[dict, list[dict]]:
    team = await create_team(client, account, team_name)
    players: list[dict] = []
    for name in player_names:
        player = await create_player(client, account, name)
        await add_to_roster(client, account, team["id"], player["id"])
        players.append(player)
    return team, players


async def create_draft(client: AsyncClient, account: dict, **payload: object) -> dict:
    body = {"format": "T20", "players_per_team": 2, **payload}
    response = await client.post("/api/v1/matches", json=body, headers=bearer(account))
    assert response.status_code == 201, response.text
    return response.json()


def xi_payload(match_team_id: str, players: list[dict], *, captain: int = 0, keeper: int = 1) -> dict:
    return {
        "match_team_id": match_team_id,
        "players": [
            {
                "player_id": player["id"],
                "is_captain": index == captain,
                "is_wicket_keeper": index == keeper,
                "batting_position": index + 1,
            }
            for index, player in enumerate(players)
        ],
    }


async def create_ready_match(
    client: AsyncClient,
    account: dict,
    *,
    format: str = "CUSTOM",
    overs: int = 1,
    balls: int = 6,
    players: int = 2,
    toss: str = "BAT",
    label: str = "Alpha",
    name: str | None = None,
    venue_name: str | None = None,
) -> dict:
    names_a = [f"{label} {index}" for index in range(players)]
    names_b = [f"{label} Opp {index}" for index in range(players)]
    team_a, players_a = await seed_squad(client, account, label, names_a)
    team_b, players_b = await seed_squad(client, account, f"{label} Opp", names_b)
    match = await create_draft(
        client,
        account,
        format=format,
        overs_per_innings=overs,
        balls_per_over=balls,
        players_per_team=players,
        name=name,
        venue_name=venue_name,
    )
    teams = (
        await client.put(
            f"/api/v1/matches/{match['id']}/teams",
            json={"team_a_id": team_a["id"], "team_b_id": team_b["id"]},
            headers=bearer(account),
        )
    ).json()
    side_a = next(item for item in teams["teams"] if item["side"] == "TEAM_A")
    side_b = next(item for item in teams["teams"] if item["side"] == "TEAM_B")
    await client.put(
        f"/api/v1/matches/{match['id']}/playing-xi",
        json={"teams": [xi_payload(side_a["id"], players_a), xi_payload(side_b["id"], players_b)]},
        headers=bearer(account),
    )
    await client.put(
        f"/api/v1/matches/{match['id']}/toss",
        json={"winner_match_team_id": side_a["id"], "decision": toss},
        headers=bearer(account),
    )
    ready = await client.post(f"/api/v1/matches/{match['id']}/ready", headers=bearer(account))
    assert ready.status_code == 200, ready.text
    body = ready.json()
    batting = next(item for item in body["teams"] if item["side"] == "TEAM_A")
    bowling = next(item for item in body["teams"] if item["side"] == "TEAM_B")
    if toss == "BOWL":
        batting, bowling = bowling, batting
    return {
        "match": body,
        "batting": batting,
        "bowling": bowling,
        "headers": bearer(account),
    }


def start_body(fixture: dict) -> dict:
    batting = fixture["batting"]["players"]
    bowling = fixture["bowling"]["players"]
    return {
        "striker_id": batting[0]["id"],
        "non_striker_id": batting[1]["id"],
        "bowler_id": bowling[0]["id"],
        "client_event_id": str(uuid4()),
    }


async def score_delivery(
    client: AsyncClient,
    match_id: str,
    headers: dict,
    revision: int,
    **fields: object,
) -> dict:
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


async def complete_simple_match(
    client: AsyncClient,
    account: dict,
    *,
    first_runs: int = 4,
    second_runs: int = 1,
    label: str = "Alpha",
    name: str | None = None,
    venue_name: str | None = None,
    match_format: str = "CUSTOM",
    players: int = 2,
    team_a_name: str | None = None,
    team_b_name: str | None = None,
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
    if team_a_name or team_b_name:
        # Names are set at team create time; create_ready_match uses label.
        pass
    match_id = fixture["match"]["id"]
    headers = fixture["headers"]
    live = (await client.post(f"/api/v1/matches/{match_id}/start", json=start_body(fixture), headers=headers)).json()
    live = await score_delivery(client, match_id, headers, live["revision"], runs_off_bat=first_runs)
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
    live = await score_delivery(client, match_id, headers, second.json()["revision"], runs_off_bat=second_runs)
    assert live["status"] == "COMPLETED"
    detail = await client.get(f"/api/v1/matches/{match_id}", headers=headers)
    scorecard = await client.get(f"/api/v1/matches/{match_id}/scorecard", headers=headers)
    assert detail.status_code == 200
    assert scorecard.status_code == 200
    return {
        "live": live,
        "detail": detail.json(),
        "scorecard": scorecard.json(),
        "fixture": fixture,
        "headers": headers,
        "match_id": match_id,
    }
