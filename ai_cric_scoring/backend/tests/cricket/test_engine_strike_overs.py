import pytest
from tests.cricket.conftest import innings, play, runs, start_match, wicket

from app.cricket.commands import DeliveryCommand, SelectBatterCommand, SelectBowlerCommand
from app.cricket.exceptions import InvalidBowlerError
from app.cricket.types import DismissalType


def test_strike_odd_even_and_over_end() -> None:
    engine, state, batting, bowling = start_match(overs=2, balls=6, players=5)
    state = play(engine, state, runs(1))
    assert innings(state).striker_id == batting[1]
    state = play(engine, state, runs(2))
    assert innings(state).striker_id == batting[1]
    state = play(engine, state, runs(3))
    assert innings(state).striker_id == batting[0]
    for _ in range(3):
        state = play(engine, state, runs(0))
    current = innings(state)
    assert current.legal_balls == 6
    assert current.needs_new_bowler
    assert current.current_bowler_id is None
    # over-ending even (dot) swaps, so the batter who faced the last ball changes ends
    assert current.striker_id == batting[1]


def test_wide_does_not_complete_over() -> None:
    engine, state, _, bowling = start_match(overs=1, balls=6, players=5)
    for _ in range(5):
        state = play(engine, state, runs(0))
    state = play(engine, state, DeliveryCommand(wides=1))
    current = innings(state)
    assert current.legal_balls == 5
    assert not current.needs_new_bowler
    assert current.current_bowler_id == bowling[0]


def test_custom_eight_ball_over() -> None:
    engine, state, _, bowling = start_match(overs=1, balls=8, players=5)
    for _ in range(8):
        state = play(engine, state, runs(0))
    current = innings(state)
    assert current.legal_balls == 8
    assert current.status.value == "COMPLETED"
    assert current.bowlers[bowling[0]].maidens == 1


def test_maiden_ignores_byes() -> None:
    engine, state, _, bowling = start_match(overs=2, balls=6, players=5)
    state = play(engine, state, DeliveryCommand(byes=1))
    for _ in range(5):
        state = play(engine, state, runs(0))
    current = innings(state)
    assert current.needs_new_bowler
    assert current.total_runs == 1
    assert current.bowlers[bowling[0]].maidens == 1
    assert current.bowlers[bowling[0]].runs_conceded == 0


def test_new_batter_and_bowler_selection() -> None:
    engine, state, batting, bowling = start_match(overs=2, balls=6, players=5)
    state = play(engine, state, wicket(batting[0], DismissalType.BOWLED))
    state = engine.select_batter(state, SelectBatterCommand(batting[2])).state
    current = innings(state)
    assert current.striker_id == batting[2]
    assert not current.needs_new_batter
    for _ in range(5):
        state = play(engine, state, runs(0))
    state = engine.select_bowler(state, SelectBowlerCommand(bowling[1])).state
    current = innings(state)
    assert current.current_bowler_id == bowling[1]
    assert not current.needs_new_bowler


def test_same_bowler_cannot_bowl_consecutive_overs() -> None:
    engine, state, _, bowling = start_match(overs=2, balls=6, players=5)
    for _ in range(6):
        state = play(engine, state, runs(0))
    with pytest.raises(InvalidBowlerError):
        engine.select_bowler(state, SelectBowlerCommand(bowling[0]))
