import pytest
from tests.cricket.conftest import innings, play, start_match, wicket

from app.cricket.commands import SelectBatterCommand
from app.cricket.exceptions import InvalidWicketForNoBallError, InvalidWicketForWideError
from app.cricket.types import DismissalType


def _select(engine, state, player):
    return engine.select_batter(state, SelectBatterCommand(player)).state


def test_bowled_credits_bowler_and_requires_new_batter() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, wicket(batting[0], DismissalType.BOWLED))
    current = innings(state)
    assert current.wickets == 1
    assert current.legal_balls == 1
    assert current.batters[batting[0]].is_out
    assert current.bowlers[bowling[0]].wickets == 1
    assert current.needs_new_batter
    assert current.fall_of_wickets[0].team_score == 0
    assert current.fall_of_wickets[0].player_id == batting[0]


def test_caught_and_lbw() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(engine, state, wicket(batting[0], DismissalType.CAUGHT, fielder=bowling[1]))
    state = _select(engine, state, batting[2])
    state = play(engine, state, wicket(batting[2], DismissalType.LBW))
    current = innings(state)
    assert current.wickets == 2
    assert current.bowlers[bowling[0]].wickets == 2


def test_run_out_striker_and_non_striker() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = play(
        engine,
        state,
        wicket(batting[1], DismissalType.RUN_OUT, fielder=bowling[1], runs_off_bat=1),
    )
    current = innings(state)
    assert current.wickets == 1
    assert current.total_runs == 1
    assert current.bowlers[bowling[0]].wickets == 0
    assert current.batters[batting[1]].is_out
    assert not current.batters[batting[0]].is_out
    state = _select(engine, state, batting[2])
    facing = innings(state).striker_id
    state = play(engine, state, wicket(facing, DismissalType.RUN_OUT, fielder=bowling[1]))
    assert innings(state).wickets == 2
    assert innings(state).bowlers[bowling[0]].wickets == 0


def test_stumped_hit_wicket_and_unusual() -> None:
    engine, state, batting, bowling = start_match(overs=4, players=8)
    state = play(engine, state, wicket(batting[0], DismissalType.STUMPED, fielder=bowling[1]))
    state = _select(engine, state, batting[2])
    state = play(engine, state, wicket(batting[2], DismissalType.HIT_WICKET))
    state = _select(engine, state, batting[3])
    state = play(engine, state, wicket(batting[3], DismissalType.OBSTRUCTING_THE_FIELD))
    state = _select(engine, state, batting[4])
    state = play(engine, state, wicket(batting[4], DismissalType.HIT_THE_BALL_TWICE))
    current = innings(state)
    assert current.wickets == 4
    assert current.bowlers[bowling[0]].wickets == 2


def test_no_ball_bowled_rejected_run_out_allowed() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    with pytest.raises(InvalidWicketForNoBallError):
        play(engine, state, wicket(batting[0], DismissalType.BOWLED, no_balls=1))
    state = play(
        engine,
        state,
        wicket(batting[1], DismissalType.RUN_OUT, fielder=bowling[1], no_balls=1),
    )
    current = innings(state)
    assert current.wickets == 1
    assert current.legal_balls == 0
    assert current.total_runs == 1
    assert current.bowlers[bowling[0]].wickets == 0


def test_wide_stumped_allowed_lbw_rejected() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    with pytest.raises(InvalidWicketForWideError):
        play(engine, state, wicket(batting[0], DismissalType.LBW, wides=1))
    state = play(engine, state, wicket(batting[0], DismissalType.STUMPED, fielder=bowling[1], wides=1))
    current = innings(state)
    assert current.wickets == 1
    assert current.legal_balls == 0
    assert current.total_runs == 1
    assert current.bowlers[bowling[0]].wickets == 1


def test_retired_hurt_is_not_a_wicket() -> None:
    from app.cricket.commands import RetireCommand

    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = engine.retire(state, RetireCommand(batting[0], hurt=True)).state
    current = innings(state)
    assert current.wickets == 0
    assert current.bowlers[bowling[0]].wickets == 0
    assert current.batters[batting[0]].is_retired_hurt
    assert not current.batters[batting[0]].is_out
    assert current.needs_new_batter
    assert current.fall_of_wickets == []


def test_retired_out_is_team_wicket_not_bowler() -> None:
    from app.cricket.commands import RetireCommand

    engine, state, batting, bowling = start_match(overs=2, players=5)
    state = engine.retire(state, RetireCommand(batting[0], hurt=False)).state
    current = innings(state)
    assert current.wickets == 1
    assert current.bowlers[bowling[0]].wickets == 0
    assert current.batters[batting[0]].is_retired_out
    assert current.fall_of_wickets[0].player_id == batting[0]
