import pytest
from tests.cricket.conftest import innings, play, start_match

from app.cricket.commands import DeliveryCommand
from app.cricket.exceptions import InvalidExtraCombinationError


def test_wide_is_illegal_and_not_balls_faced() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(wides=1))
    current = innings(state)
    assert current.total_runs == 1
    assert current.legal_balls == 0
    assert current.batters[batting[0]].balls_faced == 0
    assert current.batters[batting[0]].runs == 0
    assert current.bowlers[bowling[0]].runs_conceded == 1
    assert current.bowlers[bowling[0]].wides == 1
    assert current.striker_id == batting[0]


def test_multiple_wides_rotate_on_odd_additional_runs() -> None:
    engine, state, batting, _ = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(wides=2))
    current = innings(state)
    assert current.total_runs == 2
    assert current.legal_balls == 0
    assert current.striker_id == batting[1]


def test_no_ball_plus_batter_run() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(no_balls=1, runs_off_bat=1))
    current = innings(state)
    assert current.total_runs == 2
    assert current.legal_balls == 0
    assert current.batters[batting[0]].runs == 1
    assert current.batters[batting[0]].balls_faced == 1
    assert current.bowlers[bowling[0]].runs_conceded == 2
    assert current.bowlers[bowling[0]].no_balls == 1
    assert current.striker_id == batting[1]


def test_no_ball_boundary() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(no_balls=1, runs_off_bat=4))
    current = innings(state)
    assert current.total_runs == 5
    assert current.batters[batting[0]].fours == 1
    assert current.bowlers[bowling[0]].runs_conceded == 5
    assert current.legal_balls == 0


def test_byes_not_charged_to_bowler_or_batter() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(byes=2))
    current = innings(state)
    assert current.total_runs == 2
    assert current.legal_balls == 1
    assert current.batters[batting[0]].runs == 0
    assert current.batters[batting[0]].balls_faced == 1
    assert current.bowlers[bowling[0]].runs_conceded == 0


def test_leg_byes_not_charged_to_bowler() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(leg_byes=3))
    current = innings(state)
    assert current.total_runs == 3
    assert current.bowlers[bowling[0]].runs_conceded == 0
    assert current.batters[batting[0]].runs == 0
    assert current.striker_id == batting[1]


def test_penalty_runs_are_team_only_by_default() -> None:
    engine, state, _, bowling = start_match(overs=2, players=5)
    state = play(engine, state, DeliveryCommand(penalty_runs=5))
    current = innings(state)
    assert current.total_runs == 5
    assert current.legal_balls == 1
    assert current.bowlers[bowling[0]].runs_conceded == 0


def test_invalid_extra_combinations() -> None:
    engine, state, _, _ = start_match(overs=2, players=5)
    with pytest.raises(InvalidExtraCombinationError):
        play(engine, state, DeliveryCommand(wides=1, no_balls=1))
    with pytest.raises(InvalidExtraCombinationError):
        play(engine, state, DeliveryCommand(byes=1, leg_byes=1))
    with pytest.raises(InvalidExtraCombinationError):
        play(engine, state, DeliveryCommand(wides=-1))
