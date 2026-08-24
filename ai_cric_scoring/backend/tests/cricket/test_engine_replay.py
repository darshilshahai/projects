from tests.cricket.conftest import innings, runs, start_match, wicket

from app.cricket.commands import DeliveryCommand, SelectBatterCommand, SelectBowlerCommand
from app.cricket.engine import ScoringEngine, new_match_state
from app.cricket.events import DomainEvent
from app.cricket.replay import ScoringReplay
from app.cricket.serialization import innings_from_dict, innings_to_dict
from app.cricket.types import DismissalType, ScoringEventType


def _collect_sequence(engine: ScoringEngine, state, batting, bowling) -> tuple[list[DomainEvent], object]:
    events: list[DomainEvent] = []
    started = engine.start_innings(
        new_match_state(
            match_id=state.match_id,
            rules=state.rules,
            batting_first_team_id=state.batting_first_team_id,
            bowling_first_team_id=state.bowling_first_team_id,
        ),
        innings_number=1,
        batting_team_id=state.batting_first_team_id,
        bowling_team_id=state.bowling_first_team_id,
        batting_player_ids=tuple(batting),
        bowling_player_ids=tuple(bowling),
        striker_id=batting[0],
        non_striker_id=batting[1],
        bowler_id=bowling[0],
    )
    events.extend(started.events)
    state = started.state
    sequence = [
        runs(1),
        DeliveryCommand(wides=1),
        runs(4),
        wicket(innings(state).striker_id, DismissalType.BOWLED),
    ]
    for command in sequence:
        if command.dismissal is not None:
            command = wicket(innings(state).striker_id, DismissalType.BOWLED)
        result = engine.apply_delivery(state, command)
        events.extend(result.events)
        state = result.state
        if innings(state).needs_new_batter:
            result = engine.select_batter(state, SelectBatterCommand(batting[2]))
            events.extend(result.events)
            state = result.state
    while innings(state).legal_balls < 6 and innings(state).is_live:
        result = engine.apply_delivery(state, runs(0))
        events.extend(result.events)
        state = result.state
    if innings(state).needs_new_bowler:
        result = engine.select_bowler(state, SelectBowlerCommand(bowling[1]))
        events.extend(result.events)
        state = result.state
    return events, state


def test_replay_matches_incremental_state() -> None:
    engine, original, batting, bowling = start_match(overs=2, players=5)
    events, incremental = _collect_sequence(engine, original, batting, bowling)
    replayed = ScoringReplay(engine).replay(
        events,
        initial=new_match_state(
            match_id=original.match_id,
            rules=original.rules,
            batting_first_team_id=original.batting_first_team_id,
            bowling_first_team_id=original.bowling_first_team_id,
        ),
    )
    left = innings(incremental)
    right = innings(replayed)
    assert innings_to_dict(left) == innings_to_dict(right)


def test_voided_delivery_is_skipped_on_replay() -> None:
    engine, state, batting, bowling = start_match(overs=2, players=5)
    first = engine.apply_delivery(state, runs(4))
    second = engine.apply_delivery(first.state, runs(1))
    events = [
        DomainEvent(
            ScoringEventType.INNINGS_STARTED,
            {
                "innings_number": 1,
                "batting_team_id": str(state.batting_first_team_id),
                "bowling_team_id": str(state.bowling_first_team_id),
                "batting_player_ids": [str(item) for item in batting],
                "bowling_player_ids": [str(item) for item in bowling],
                "striker_id": str(batting[0]),
                "non_striker_id": str(batting[1]),
                "bowler_id": str(bowling[0]),
                "target_runs": None,
            },
        ),
        *first.events,
        *second.events,
        DomainEvent(ScoringEventType.DELIVERY_VOIDED, {"target_sequence": 2}),
    ]
    replayed = ScoringReplay(engine).replay(
        events,
        initial=new_match_state(
            match_id=state.match_id,
            rules=state.rules,
            batting_first_team_id=state.batting_first_team_id,
            bowling_first_team_id=state.bowling_first_team_id,
        ),
    )
    current = innings(replayed)
    assert current.total_runs == 4
    assert current.legal_balls == 1
    assert current.striker_id == batting[0]


def test_innings_dict_round_trip() -> None:
    _, state, _, _ = start_match(overs=2, players=5)
    restored = innings_from_dict(innings_to_dict(innings(state)))
    assert innings_to_dict(restored) == innings_to_dict(innings(state))
