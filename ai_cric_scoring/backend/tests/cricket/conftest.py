from __future__ import annotations

from uuid import UUID, uuid4

from app.cricket.commands import DeliveryCommand, DismissalCommand
from app.cricket.engine import ScoringEngine, new_match_state
from app.cricket.rules import MatchRules
from app.cricket.state import InningsState, MatchState
from app.cricket.types import DismissalType


def ids(count: int) -> list[UUID]:
    return [uuid4() for _ in range(count)]


def mini_rules(*, overs: int = 2, balls: int = 6, players: int = 5) -> MatchRules:
    return MatchRules(
        overs_per_innings=overs,
        balls_per_over=balls,
        players_per_team=players,
        format="CUSTOM",
    )


def start_match(
    engine: ScoringEngine | None = None,
    *,
    overs: int = 20,
    balls: int = 6,
    players: int = 11,
    batting: list[UUID] | None = None,
    bowling: list[UUID] | None = None,
) -> tuple[ScoringEngine, MatchState, list[UUID], list[UUID]]:
    engine = engine or ScoringEngine()
    batting_ids = batting or ids(players)
    bowling_ids = bowling or ids(players)
    team_a, team_b = uuid4(), uuid4()
    state = new_match_state(
        match_id=uuid4(),
        rules=mini_rules(overs=overs, balls=balls, players=players),
        batting_first_team_id=team_a,
        bowling_first_team_id=team_b,
    )
    result = engine.start_innings(
        state,
        innings_number=1,
        batting_team_id=team_a,
        bowling_team_id=team_b,
        batting_player_ids=tuple(batting_ids),
        bowling_player_ids=tuple(bowling_ids),
        striker_id=batting_ids[0],
        non_striker_id=batting_ids[1],
        bowler_id=bowling_ids[0],
    )
    return engine, result.state, batting_ids, bowling_ids


def innings(state: MatchState) -> InningsState:
    current = state.current_innings
    assert current is not None
    return current


def play(engine: ScoringEngine, state: MatchState, command: DeliveryCommand) -> MatchState:
    return engine.apply_delivery(state, command).state


def runs(value: int) -> DeliveryCommand:
    return DeliveryCommand(runs_off_bat=value)


def wicket(
    dismissed: UUID,
    kind: DismissalType = DismissalType.BOWLED,
    *,
    fielder: UUID | None = None,
    crossed: bool = False,
    **extras: int,
) -> DeliveryCommand:
    return DeliveryCommand(
        dismissal=DismissalCommand(
            type=kind,
            dismissed_player_id=dismissed,
            fielder_id=fielder,
            crossed=crossed,
        ),
        **extras,
    )
