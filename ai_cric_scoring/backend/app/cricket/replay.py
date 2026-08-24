from __future__ import annotations

from typing import Any
from uuid import UUID

from app.cricket.commands import (
    DeliveryCommand,
    DismissalCommand,
    RetireCommand,
    SelectBatterCommand,
    SelectBowlerCommand,
)
from app.cricket.engine import EngineResult, ScoringEngine, new_match_state
from app.cricket.events import DomainEvent
from app.cricket.rules import MatchRules
from app.cricket.state import MatchState
from app.cricket.types import DismissalType, ScoringEventType


class ScoringReplay:
    def __init__(self, engine: ScoringEngine | None = None) -> None:
        self._engine = engine or ScoringEngine()

    def replay(self, events: list[DomainEvent], *, initial: MatchState) -> MatchState:
        state = initial
        voided: set[int] = set()
        indexed = list(enumerate(events))
        for _index, event in indexed:
            if event.type == ScoringEventType.DELIVERY_VOIDED:
                target = event.payload.get("target_sequence")
                if isinstance(target, int):
                    voided.add(target)
        for index, event in indexed:
            sequence = event.sequence_number if event.sequence_number is not None else index
            if sequence in voided or event.type == ScoringEventType.DELIVERY_VOIDED:
                continue
            if event.type in {ScoringEventType.INNINGS_COMPLETED, ScoringEventType.MATCH_COMPLETED}:
                continue
            result = self._apply(state, event)
            if result is not None:
                state = result.state
        return state

    def _apply(self, state: MatchState, event: DomainEvent) -> EngineResult | None:
        payload = event.payload
        if event.type == ScoringEventType.INNINGS_STARTED:
            return self._engine.start_innings(
                state,
                innings_number=int(payload["innings_number"]),
                batting_team_id=UUID(str(payload["batting_team_id"])),
                bowling_team_id=UUID(str(payload["bowling_team_id"])),
                batting_player_ids=tuple(UUID(str(item)) for item in payload["batting_player_ids"]),
                bowling_player_ids=tuple(UUID(str(item)) for item in payload["bowling_player_ids"]),
                striker_id=UUID(str(payload["striker_id"])),
                non_striker_id=UUID(str(payload["non_striker_id"])),
                bowler_id=UUID(str(payload["bowler_id"])),
                target_runs=payload.get("target_runs"),
            )
        if event.type == ScoringEventType.DELIVERY_RECORDED:
            return self._engine.apply_delivery(state, _delivery_from_payload(payload))
        if event.type == ScoringEventType.BATTER_SELECTED:
            return self._engine.select_batter(state, SelectBatterCommand(UUID(str(payload["player_id"]))))
        if event.type == ScoringEventType.BOWLER_SELECTED:
            return self._engine.select_bowler(state, SelectBowlerCommand(UUID(str(payload["player_id"]))))
        if event.type == ScoringEventType.BATTER_RETIRED:
            return self._engine.retire(
                state,
                RetireCommand(UUID(str(payload["player_id"])), hurt=bool(payload.get("hurt", True))),
            )
        return None


def _delivery_from_payload(payload: dict[str, Any]) -> DeliveryCommand:
    raw = payload.get("dismissal")
    dismissal = None
    if isinstance(raw, dict):
        fielder = raw.get("fielder_id")
        dismissal = DismissalCommand(
            type=DismissalType(str(raw["type"])),
            dismissed_player_id=UUID(str(raw["dismissed_player_id"])),
            fielder_id=UUID(str(fielder)) if fielder else None,
            crossed=bool(raw.get("crossed", False)),
        )
    return DeliveryCommand(
        runs_off_bat=int(payload.get("runs_off_bat", 0)),
        wides=int(payload.get("wides", 0)),
        no_balls=int(payload.get("no_balls", 0)),
        byes=int(payload.get("byes", 0)),
        leg_byes=int(payload.get("leg_byes", 0)),
        penalty_runs=int(payload.get("penalty_runs", 0)),
        dismissal=dismissal,
    )


def empty_match(
    rules: MatchRules,
    batting_first: UUID,
    bowling_first: UUID,
    match_id: UUID | None = None,
) -> MatchState:
    from uuid import uuid4

    return new_match_state(
        match_id=match_id or uuid4(),
        rules=rules,
        batting_first_team_id=batting_first,
        bowling_first_team_id=bowling_first,
    )
