from tests.cricket.conftest import innings, play, runs, start_match, wicket

from app.cricket.commands import DeliveryCommand, SelectBatterCommand, SelectBowlerCommand
from app.cricket.formatters import required_run_rate, run_rate
from app.cricket.state import BowlerState
from app.cricket.types import DismissalType, MatchPlayStatus, ResultType


def test_run_rate_uses_legal_balls_not_decimal_overs() -> None:
    assert run_rate(30, 24, 6) == 7.5
    assert run_rate(30, 24, 8) == 10.0
    assert run_rate(10, 0, 6) is None


def test_required_run_rate_example() -> None:
    assert (
        required_run_rate(
            target_runs=101,
            current_runs=60,
            maximum_legal_balls=90,
            legal_balls=60,
            balls_per_over=6,
        )
        == 8.2
    )
    assert (
        required_run_rate(
            target_runs=101,
            current_runs=101,
            maximum_legal_balls=90,
            legal_balls=80,
            balls_per_over=6,
        )
        == 0.0
    )
    assert (
        required_run_rate(
            target_runs=101,
            current_runs=90,
            maximum_legal_balls=90,
            legal_balls=90,
            balls_per_over=6,
        )
        is None
    )


def test_small_team_all_out() -> None:
    engine, state, batting, _ = start_match(overs=5, balls=6, players=5)
    next_batter = 2
    for _ in range(4):
        dismissed = innings(state).striker_id
        assert dismissed is not None
        state = play(engine, state, wicket(dismissed, DismissalType.BOWLED))
        if innings(state).needs_new_batter:
            state = engine.select_batter(state, SelectBatterCommand(batting[next_batter])).state
            next_batter += 1
    current = innings(state)
    assert current.wickets == 4
    assert current.status.value == "COMPLETED"
    assert not current.needs_new_batter


def test_custom_overs_complete_innings() -> None:
    engine, state, _, _ = start_match(overs=3, balls=5, players=5)
    for _ in range(15):
        state = play(engine, state, runs(1))
        current = innings(state)
        if current.needs_new_bowler:
            bowling_ids = list(current.bowling_player_ids)
            nxt = next(
                item
                for item in bowling_ids
                if item != current.previous_bowler_id
                and current.bowlers.get(item, BowlerState(item)).legal_balls < state.rules.bowler_max_legal_balls
            )
            state = engine.select_bowler(state, SelectBowlerCommand(nxt)).state
    current = innings(state)
    assert current.legal_balls == 15
    assert current.status.value == "COMPLETED"
    assert current.total_runs == 15


def test_partnership_and_fall_of_wicket() -> None:
    engine, state, batting, _ = start_match(overs=2, players=5)
    state = play(engine, state, runs(4))
    state = play(engine, state, DeliveryCommand(wides=1))
    assert innings(state).current_partnership is not None
    assert innings(state).current_partnership.runs == 5
    state = play(engine, state, wicket(batting[0], DismissalType.BOWLED))
    current = innings(state)
    assert current.current_partnership is None
    assert current.fall_of_wickets[0].team_score == 5
    assert current.fall_of_wickets[0].player_id == batting[0]
    state = engine.select_batter(state, SelectBatterCommand(batting[2])).state
    assert innings(state).current_partnership is not None
    assert innings(state).current_partnership.start_score == 5


def test_chase_win_by_wickets() -> None:
    engine, state, batting, bowling = start_match(overs=1, balls=2, players=3)
    state = play(engine, state, runs(4))
    state = play(engine, state, runs(0))
    assert innings(state).status.value == "COMPLETED"
    first_total = innings(state).total_runs
    result = engine.start_innings(
        state,
        innings_number=2,
        batting_team_id=state.bowling_first_team_id,
        bowling_team_id=state.batting_first_team_id,
        batting_player_ids=tuple(bowling),
        bowling_player_ids=tuple(batting),
        striker_id=bowling[0],
        non_striker_id=bowling[1],
        bowler_id=batting[0],
        target_runs=first_total + 1,
    )
    state = play(engine, result.state, runs(6))
    current = innings(state)
    assert current.target_runs is not None
    assert current.total_runs >= current.target_runs
    assert state.status == MatchPlayStatus.COMPLETED
    assert state.result_type == ResultType.WON
    assert state.winner_team_id == state.bowling_first_team_id
    assert state.margin_wickets == 2


def test_defending_win_by_runs() -> None:
    engine, state, batting, bowling = start_match(overs=1, balls=1, players=3)
    state = play(engine, state, runs(6))
    first_total = innings(state).total_runs
    result = engine.start_innings(
        state,
        innings_number=2,
        batting_team_id=state.bowling_first_team_id,
        bowling_team_id=state.batting_first_team_id,
        batting_player_ids=tuple(bowling),
        bowling_player_ids=tuple(batting),
        striker_id=bowling[0],
        non_striker_id=bowling[1],
        bowler_id=batting[0],
        target_runs=first_total + 1,
    )
    state = play(engine, result.state, runs(1))
    assert state.status == MatchPlayStatus.COMPLETED
    assert state.result_type == ResultType.WON
    assert state.winner_team_id == state.batting_first_team_id
    assert state.margin_runs == 5


def test_tie() -> None:
    engine, state, batting, bowling = start_match(overs=1, balls=1, players=3)
    state = play(engine, state, runs(2))
    result = engine.start_innings(
        state,
        innings_number=2,
        batting_team_id=state.bowling_first_team_id,
        bowling_team_id=state.batting_first_team_id,
        batting_player_ids=tuple(bowling),
        bowling_player_ids=tuple(batting),
        striker_id=bowling[0],
        non_striker_id=bowling[1],
        bowler_id=batting[0],
        target_runs=3,
    )
    state = play(engine, result.state, runs(2))
    assert state.status == MatchPlayStatus.COMPLETED
    assert state.result_type == ResultType.TIED
    assert state.winner_team_id is None


def test_no_delivery_after_innings_complete() -> None:
    engine, state, _, _ = start_match(overs=1, balls=1, players=3)
    state = play(engine, state, runs(1))
    try:
        play(engine, state, runs(1))
    except Exception as exc:
        assert "complete" in str(exc).lower()
    else:
        raise AssertionError("expected innings complete rejection")
