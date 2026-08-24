"""Deterministic evaluation fact packages. Used by tests and the optional script."""

from __future__ import annotations

from uuid import uuid4

from app.ai.context.fact_package import MatchFactPackage, assemble_fact_package
from app.cricket.types import InningsStatus, ResultType
from app.models.enums import MatchFormat, MatchStatus
from app.schemas.scorecard import (
    BattingScorecardRow,
    BowlingScorecardRow,
    ExtrasScorecard,
    FallOfWicketRow,
    InningsScorecard,
    MatchScorecardResponse,
    OverSummaryRow,
    PartnershipRow,
    ScorecardMatchHeader,
    ScorecardTeam,
)


def _team(name: str) -> ScorecardTeam:
    return ScorecardTeam(match_team_id=uuid4(), name=name)


def _batter(name: str, runs: int, balls: int, **extra: object) -> BattingScorecardRow:
    return BattingScorecardRow(
        match_player_id=uuid4(),
        name=name,
        batting_position=1,
        runs=runs,
        balls=balls,
        fours=int(extra.get("fours", 0)),
        sixes=int(extra.get("sixes", 0)),
        strike_rate=round(runs / balls * 100, 2) if balls else 0,
        status=str(extra.get("status", "out")),
        dismissal_text=str(extra.get("dismissal", "b bowler")),
    )


def _bowler(name: str, wickets: int, runs: int) -> BowlingScorecardRow:
    return BowlingScorecardRow(
        match_player_id=uuid4(),
        name=name,
        legal_balls=24,
        overs="4.0",
        maidens=0,
        runs_conceded=runs,
        wickets=wickets,
        economy=7.0,
        wides=0,
        no_balls=0,
    )


def _innings(
    number: int,
    batting: ScorecardTeam,
    bowling: ScorecardTeam,
    runs: int,
    wickets: int,
    batters: list[BattingScorecardRow],
    bowlers: list[BowlingScorecardRow],
    fow: list[FallOfWicketRow],
    partnerships: list[PartnershipRow],
    overs: list[OverSummaryRow],
    target: int | None = None,
) -> InningsScorecard:
    return InningsScorecard(
        id=uuid4(),
        number=number,
        status=InningsStatus.COMPLETED,
        batting_team=batting,
        bowling_team=bowling,
        runs=runs,
        wickets=wickets,
        legal_balls=120,
        overs="20.0",
        run_rate=8.7,
        target=target,
        extras=ExtrasScorecard(total=4, wides=4, no_balls=0, byes=0, leg_byes=0, penalty_runs=0),
        batting=batters,
        bowling=bowlers,
        fall_of_wickets=fow,
        partnerships=partnerships,
        overs_summary=overs,
    )


def _over(number: int, runs: int, wickets: int = 0) -> OverSummaryRow:
    return OverSummaryRow(
        over_number=number,
        runs=runs,
        wickets=wickets,
        legal_balls=6,
        is_complete=True,
    )


def _package(header: ScorecardMatchHeader, innings: list[InningsScorecard]) -> MatchFactPackage:
    return assemble_fact_package(MatchScorecardResponse(match=header, status=MatchStatus.COMPLETED, innings=innings))


def _header(
    team_a: ScorecardTeam,
    team_b: ScorecardTeam,
    winner: ScorecardTeam | None,
    *,
    tied: bool = False,
) -> ScorecardMatchHeader:
    return ScorecardMatchHeader(
        id=uuid4(),
        name="Eval Match",
        format=MatchFormat.T20,
        status=MatchStatus.COMPLETED,
        venue_name="Eval Ground",
        overs_per_innings=20,
        balls_per_over=6,
        players_per_team=11,
        team_a=team_a,
        team_b=team_b,
        result_type=ResultType.TIED if tied else ResultType.WON,
        winner_match_team_id=None if tied else winner.match_team_id if winner else None,
        winner_name=None if tied else winner.name if winner else None,
        margin_runs=None if tied or winner is None else 12,
    )


def defending_win_after_cluster() -> MatchFactPackage:
    team_a = _team("Defenders")
    team_b = _team("Chasers")
    batter = _batter("Anchor", 40, 38)
    bowler = _bowler("Strike", 3, 18)
    fow = [
        FallOfWicketRow(wicket_number=1, score=30, player_id=uuid4(), player_name="A", legal_balls=40, overs="6.4"),
        FallOfWicketRow(wicket_number=2, score=34, player_id=uuid4(), player_name="B", legal_balls=46, overs="7.4"),
        FallOfWicketRow(wicket_number=3, score=38, player_id=uuid4(), player_name="C", legal_balls=50, overs="8.2"),
    ]
    innings = [
        _innings(1, team_a, team_b, 140, 6, [batter], [bowler], [], [], [_over(20, 8)]),
        _innings(
            2,
            team_b,
            team_a,
            128,
            8,
            [_batter("Chase", 22, 18)],
            [bowler],
            fow,
            [],
            [_over(8, 2, 2)],
            target=141,
        ),
    ]
    return _package(_header(team_a, team_b, team_a), innings)


def chase_through_partnership() -> MatchFactPackage:
    team_a = _team("Setters")
    team_b = _team("Hunters")
    a = _batter("Rahul", 62, 41, fours=6, sixes=2)
    b = _batter("Dev", 48, 36, fours=4)
    stand = PartnershipRow(
        batter_1_id=a.match_player_id,
        batter_1_name=a.name,
        batter_2_id=b.match_player_id,
        batter_2_name=b.name,
        runs=88,
        legal_balls=60,
        start_score=20,
        end_score=108,
        is_current=False,
        batter_1_runs=50,
        batter_2_runs=38,
    )
    innings = [
        _innings(
            1,
            team_a,
            team_b,
            150,
            7,
            [_batter("Opener", 30, 28)],
            [_bowler("Seam", 1, 30)],
            [],
            [],
            [_over(20, 10, 1)],
        ),
        _innings(
            2,
            team_b,
            team_a,
            151,
            4,
            [a, b],
            [_bowler("Spin", 2, 32)],
            [],
            [stand],
            [_over(19, 14)],
            target=151,
        ),
    ]
    return _package(_header(team_a, team_b, team_b), innings)


def low_scoring_tie() -> MatchFactPackage:
    team_a = _team("Left")
    team_b = _team("Right")
    header = _header(team_a, team_b, None, tied=True)
    header.margin_runs = None
    innings = [
        _innings(
            1,
            team_a,
            team_b,
            98,
            9,
            [_batter("Grit", 24, 40)],
            [_bowler("Tight", 3, 16)],
            [],
            [],
            [_over(20, 3, 1)],
        ),
        _innings(
            2,
            team_b,
            team_a,
            98,
            8,
            [_batter("Reply", 20, 32)],
            [_bowler("Hold", 2, 18)],
            [],
            [],
            [_over(20, 4)],
            target=99,
        ),
    ]
    return _package(header, innings)


def one_player_dominant() -> MatchFactPackage:
    team_a = _team("Stars")
    team_b = _team("Support")
    star = _batter("Star Batter", 92, 54, fours=8, sixes=4)
    star_bowl = _bowler("Star Batter", 3, 20)
    star_bowl.match_player_id = star.match_player_id
    innings = [
        _innings(1, team_a, team_b, 168, 5, [star], [_bowler("Opp", 1, 40)], [], [], [_over(18, 18)]),
        _innings(
            2,
            team_b,
            team_a,
            140,
            8,
            [_batter("Reply", 28, 22)],
            [star_bowl],
            [],
            [],
            [_over(16, 6, 2)],
            target=169,
        ),
    ]
    return _package(_header(team_a, team_b, team_a), innings)


def balanced_team_win() -> MatchFactPackage:
    team_a = _team("Balance")
    team_b = _team("Even")
    innings = [
        _innings(
            1,
            team_a,
            team_b,
            155,
            6,
            [_batter("One", 34, 28), _batter("Two", 31, 26)],
            [_bowler("Three", 2, 24)],
            [],
            [],
            [_over(12, 11)],
        ),
        _innings(
            2,
            team_b,
            team_a,
            142,
            7,
            [_batter("Four", 29, 24)],
            [_bowler("Five", 2, 22)],
            [],
            [],
            [_over(19, 7, 1)],
            target=156,
        ),
    ]
    return _package(_header(team_a, team_b, team_a), innings)


EVAL_FIXTURES = {
    "defending_win_after_cluster": defending_win_after_cluster,
    "chase_through_partnership": chase_through_partnership,
    "low_scoring_tie": low_scoring_tie,
    "one_player_dominant": one_player_dominant,
    "balanced_team_win": balanced_team_win,
}
