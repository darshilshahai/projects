import pytest
from tests.cricket.conftest import innings, play, runs, start_match

from app.cricket.commands import DeliveryCommand
from app.cricket.exceptions import InvalidExtraCombinationError


def test_dot_and_scoring_runs() -> None:
    engine, state, batting, bowling = start_match(overs=2, balls=8, players=5)
    for value in (0, 1, 2, 3, 4, 5, 6):
        state = play(engine, state, runs(value))
    current = innings(state)
    assert current.total_runs == 21
    assert current.legal_balls == 7
    batter = current.batters[batting[0]]
    # strike rotates on odd: 0 stay, 1 swap, so batter 0 faced 0,2,4,6?
    # 0 even stay; 1 odd swap; 2 faced by other; etc.
    assert current.total_runs == 0 + 1 + 2 + 3 + 4 + 5 + 6
    assert batter.fours + current.batters[batting[1]].fours == 1
    assert batter.sixes + current.batters[batting[1]].sixes == 1
    bowler = current.bowlers[bowling[0]]
    assert bowler.runs_conceded == 21
    assert bowler.legal_balls == 7


def test_four_and_six_are_batter_boundaries_only() -> None:
    engine, state, batting, _ = start_match(overs=2, players=5)
    state = play(engine, state, runs(4))
    state = play(engine, state, DeliveryCommand(wides=4))
    current = innings(state)
    striker = current.batters[batting[0]]
    assert striker.runs == 4
    assert striker.fours == 1
    assert striker.sixes == 0
    assert striker.balls_faced == 1
    assert current.total_runs == 8
    assert current.legal_balls == 1


def test_negative_runs_rejected() -> None:
    engine, state, _, _ = start_match(overs=2, players=5)
    with pytest.raises(InvalidExtraCombinationError):
        play(engine, state, DeliveryCommand(runs_off_bat=-1))
