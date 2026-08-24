from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.api_helpers import register_user
from tests.match_helpers import complete_simple_match

from app.ai.context.fact_package import assemble_fact_package
from app.cricket.types import InningsStatus, ResultType
from app.models.enums import MatchFormat, MatchStatus
from app.schemas.scorecard import (
    BattingScorecardRow,
    BowlingScorecardRow,
    ExtrasScorecard,
    FallOfWicketRow,
    InningsScorecard,
    MatchScorecardResponse,
    MatchScorecardSummary,
    OverSummaryRow,
    PartnershipRow,
    ScorecardMatchHeader,
    ScorecardTeam,
)


def _scorecard(*, team_a: str = "Weekend Warriors", batter: str = "Rahul Shah") -> MatchScorecardResponse:
    team_a_id = uuid4()
    team_b_id = uuid4()
    batter_id = uuid4()
    bowler_id = uuid4()
    partner_id = uuid4()
    return MatchScorecardResponse(
        match=ScorecardMatchHeader(
            id=uuid4(),
            name="Sunday Final",
            format=MatchFormat.T20,
            status=MatchStatus.COMPLETED,
            venue_name="Central Ground",
            overs_per_innings=20,
            balls_per_over=6,
            players_per_team=11,
            team_a=ScorecardTeam(match_team_id=team_a_id, name=team_a),
            team_b=ScorecardTeam(match_team_id=team_b_id, name="Office XI"),
            result_type=ResultType.WON,
            winner_match_team_id=team_a_id,
            winner_name=team_a,
            margin_runs=12,
        ),
        status=MatchStatus.COMPLETED,
        innings=[
            InningsScorecard(
                id=uuid4(),
                number=1,
                status=InningsStatus.COMPLETED,
                batting_team=ScorecardTeam(match_team_id=team_a_id, name=team_a),
                bowling_team=ScorecardTeam(match_team_id=team_b_id, name="Office XI"),
                runs=174,
                wickets=2,
                legal_balls=120,
                overs="20.0",
                run_rate=8.7,
                extras=ExtrasScorecard(total=6, wides=4, no_balls=2, byes=0, leg_byes=0, penalty_runs=0),
                batting=[
                    BattingScorecardRow(
                        match_player_id=batter_id,
                        name=batter,
                        batting_position=1,
                        runs=62,
                        balls=41,
                        fours=6,
                        sixes=2,
                        strike_rate=151.22,
                        status="out",
                        dismissal_text="b Dev",
                    )
                ],
                bowling=[
                    BowlingScorecardRow(
                        match_player_id=bowler_id,
                        name="Dev Patel",
                        legal_balls=24,
                        overs="4.0",
                        maidens=0,
                        runs_conceded=28,
                        wickets=2,
                        economy=7.0,
                        wides=1,
                        no_balls=0,
                    )
                ],
                fall_of_wickets=[
                    FallOfWicketRow(
                        wicket_number=1,
                        score=32,
                        player_id=batter_id,
                        player_name=batter,
                        legal_balls=26,
                        overs="4.2",
                    )
                ],
                partnerships=[
                    PartnershipRow(
                        batter_1_id=batter_id,
                        batter_1_name=batter,
                        batter_2_id=partner_id,
                        batter_2_name="Arjun Patel",
                        runs=68,
                        legal_balls=43,
                        start_score=32,
                        end_score=100,
                        is_current=False,
                        batter_1_runs=40,
                        batter_2_runs=28,
                    )
                ],
                overs_summary=[
                    OverSummaryRow(over_number=1, runs=8, wickets=0, legal_balls=6, is_complete=True),
                    OverSummaryRow(over_number=17, runs=16, wickets=1, legal_balls=6, is_complete=True),
                ],
            )
        ],
        summary=MatchScorecardSummary(),
    )


def test_fact_package_uses_scorecard_snapshots_and_ids() -> None:
    scorecard = _scorecard()
    package = assemble_fact_package(scorecard)
    ids = package.fact_ids()
    assert "result" in ids
    assert any(item.type == "batting" and item.values["runs"] == 62 for item in package.facts)
    assert any(item.type == "bowling" and item.values["wickets"] == 2 for item in package.facts)
    assert any(item.type == "partnership" and item.values["runs"] == 68 for item in package.facts)
    assert any(item.type == "fall_of_wicket" and item.values["score"] == 32 for item in package.facts)
    assert any(item.type == "over" and item.over_number == 17 for item in package.facts)
    assert any(item.type == "phase" for item in package.facts)
    assert any(item.type == "key_event" for item in package.facts)
    assert package.result.winner_name == "Weekend Warriors"
    assert package.potm_candidates
    context = package.to_prompt_context()
    assert "deliveries" not in str(context["over_summaries"])


@pytest.mark.asyncio
async def test_fact_package_keeps_snapshots_after_rename(auth_client: AsyncClient) -> None:
    owner = await register_user(auth_client, "facts@example.com")
    completed = await complete_simple_match(
        auth_client,
        owner,
        first_runs=4,
        second_runs=1,
        label="Snapshot",
        name="Snapshot Cup",
    )
    scorecard = completed["scorecard"]
    team_id = completed["fixture"]["match"]["teams"][0]["team_id"]
    player_id = completed["fixture"]["batting"]["players"][0]["player_id"]
    original_team = scorecard["match"]["team_a"]["name"]
    original_batter = scorecard["innings"][0]["batting"][0]["name"]
    await auth_client.patch(
        f"/api/v1/teams/{team_id}",
        json={"name": "Renamed CC"},
        headers=completed["headers"],
    )
    await auth_client.patch(
        f"/api/v1/players/{player_id}",
        json={"name": "Renamed Player"},
        headers=completed["headers"],
    )
    refreshed = await auth_client.get(
        f"/api/v1/matches/{completed['match_id']}/scorecard",
        headers=completed["headers"],
    )
    assert refreshed.status_code == 200
    package = assemble_fact_package(MatchScorecardResponse.model_validate(refreshed.json()))
    assert package.match.team_a_name == original_team
    assert any(item.label == original_batter for item in package.facts if item.type == "batting")
    assert "Renamed CC" not in {item.label for item in package.facts if item.type == "team"}
