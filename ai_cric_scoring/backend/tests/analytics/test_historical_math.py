from datetime import UTC, datetime
from uuid import uuid4

from app.analytics.history.batting import aggregate_batting
from app.analytics.history.bowling import aggregate_bowling
from app.analytics.history.definitions import is_dismissal, win_percentage
from app.analytics.history.form import batting_form_entries
from app.analytics.history.phases import aggregate_closing_phase
from app.analytics.history.rankings import RankingCandidate, sort_leaderboard
from app.analytics.history.teams import aggregate_team
from app.analytics.history.types import BattingInningsRow, BowlingInningsRow, TeamMatchRow


def _bat(runs: int, balls: int, status: str, *, when: datetime | None = None) -> BattingInningsRow:
    return BattingInningsRow(
        match_id=uuid4(),
        player_id=uuid4(),
        runs=runs,
        balls_faced=balls,
        fours=0,
        sixes=0,
        status=status,
        completed_at=when,
    )


def test_batting_average_excludes_not_outs() -> None:
    career = aggregate_batting(
        [_bat(40, 30, "OUT"), _bat(60, 40, "BATTING"), _bat(20, 20, "OUT")],
        matches_played=3,
    )
    assert career.runs == 120
    assert career.dismissals == 2
    assert career.not_outs == 1
    assert career.batting_average == 60.0
    assert career.matches == 3
    assert career.innings == 3


def test_strike_rate_uses_aggregate_balls() -> None:
    career = aggregate_batting([_bat(100, 80, "OUT")], matches_played=1)
    assert career.strike_rate == 125.0


def test_zero_dismissals_average_is_unavailable() -> None:
    career = aggregate_batting([_bat(100, 70, "BATTING")], matches_played=1)
    assert career.dismissals == 0
    assert career.batting_average is None


def test_retired_hurt_is_not_a_dismissal() -> None:
    career = aggregate_batting([_bat(22, 18, "RETIRED_HURT"), _bat(40, 30, "OUT")], matches_played=2)
    assert not is_dismissal("RETIRED_HURT")
    assert career.dismissals == 1
    assert career.not_outs == 1
    assert career.batting_average == 62.0


def test_did_not_bat_is_not_an_innings() -> None:
    career = aggregate_batting([], matches_played=4)
    assert career.matches == 4
    assert career.innings == 0
    assert career.batting_average is None


def test_bowling_average_and_economy() -> None:
    rows = [
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=uuid4(),
            legal_balls=72,
            runs_conceded=96,
            wickets=5,
            wides=2,
            no_balls=1,
            maidens=0,
            balls_per_over=6,
        )
    ]
    career = aggregate_bowling(rows, matches_played=1)
    assert career.bowling_average == 19.2
    assert career.economy == 8.0
    assert career.mixed_rules is False


def test_bowling_average_one_hundred_from_five_wickets() -> None:
    rows = [
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=uuid4(),
            legal_balls=60,
            runs_conceded=100,
            wickets=5,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        )
    ]
    assert aggregate_bowling(rows, matches_played=1).bowling_average == 20.0


def test_bowling_average_without_wickets_is_unavailable() -> None:
    rows = [
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=uuid4(),
            legal_balls=24,
            runs_conceded=40,
            wickets=0,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        )
    ]
    assert aggregate_bowling(rows, matches_played=1).bowling_average is None


def test_mixed_balls_per_over_skips_economy() -> None:
    player = uuid4()
    rows = [
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=player,
            legal_balls=30,
            runs_conceded=40,
            wickets=1,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        ),
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=player,
            legal_balls=20,
            runs_conceded=25,
            wickets=1,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=5,
        ),
    ]
    career = aggregate_bowling(rows, matches_played=2)
    assert career.mixed_rules is True
    assert career.economy is None
    assert career.runs_per_legal_ball is not None


def test_best_bowling_tie_break_fewer_runs() -> None:
    player = uuid4()
    rows = [
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=player,
            legal_balls=24,
            runs_conceded=20,
            wickets=3,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        ),
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=player,
            legal_balls=24,
            runs_conceded=15,
            wickets=3,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        ),
        BowlingInningsRow(
            match_id=uuid4(),
            player_id=player,
            legal_balls=18,
            runs_conceded=8,
            wickets=2,
            wides=0,
            no_balls=0,
            maidens=0,
            balls_per_over=6,
        ),
    ]
    assert aggregate_bowling(rows, matches_played=3).best_bowling == "3/15"


def test_win_percentage_includes_ties() -> None:
    assert win_percentage(6, 10) == 60.0
    team_id = uuid4()
    match_team = uuid4()
    rows = []
    for index, code in enumerate(["W"] * 6 + ["L"] * 3 + ["T"]):
        winner = match_team if code == "W" else (None if code == "T" else uuid4())
        rows.append(
            TeamMatchRow(
                match_id=uuid4(),
                team_id=team_id,
                match_team_id=match_team,
                completed_at=datetime(2026, 1, index + 1, tzinfo=UTC),
                format="T20",
                result_type="TIED" if code == "T" else "WON",
                winner_match_team_id=winner,
                batting_innings_number=1,
                runs_scored=150,
                wickets_lost=5,
                runs_conceded=140,
                opponent_name="Opp",
                opponent_team_id=uuid4(),
            )
        )
    career = aggregate_team(rows)
    assert career.wins == 6
    assert career.losses == 3
    assert career.ties == 1
    assert career.win_percentage == 60.0
    assert career.matches_defending == 10
    assert career.wins_defending == 6


def test_last_n_form_uses_most_recent_completed() -> None:
    rows = [_bat(index, 10, "OUT", when=datetime(2026, 1, index + 1, tzinfo=UTC)) for index in range(8)]
    form = batting_form_entries(rows, last_n=5)
    assert [item["runs"] for item in form] == [7, 6, 5, 4, 3]


def test_economy_qualification_excludes_tiny_samples() -> None:
    tiny = RankingCandidate(player_id=uuid4(), name="Dot", legal_balls=1, runs_conceded=0, balls_per_over=6)
    qualified = RankingCandidate(
        player_id=uuid4(),
        name="Dev",
        legal_balls=24,
        runs_conceded=24,
        balls_per_over=6,
        wickets=1,
    )
    ranked = sort_leaderboard("economy", [tiny, qualified])
    assert len(ranked) == 1
    assert ranked[0][0].name == "Dev"


def test_closing_phase_unsupported_for_single_over_custom() -> None:
    match_id = uuid4()
    assert aggregate_closing_phase([(match_id, 1, "CUSTOM", 1, 12)]) is None


def test_closing_phase_sums_t20_death_overs() -> None:
    match_id = uuid4()
    rows = [(match_id, 20, "T20", over, 6) for over in range(1, 21)]
    result = aggregate_closing_phase(rows)
    assert result is not None
    assert result["matches"] == 1
    assert result["runs"] == 30
