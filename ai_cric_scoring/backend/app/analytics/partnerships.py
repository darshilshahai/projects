from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from app.analytics.types import DeliveryFact, PartnershipFact


@dataclass
class _OpenPartnership:
    batter_1_id: UUID
    batter_2_id: UUID
    start_score: int
    runs: int = 0
    legal_balls: int = 0
    batter_1_runs: int = 0
    batter_2_runs: int = 0
    pair: frozenset[UUID] = field(init=False)

    def __post_init__(self) -> None:
        self.pair = frozenset({self.batter_1_id, self.batter_2_id})

    def add(self, delivery: DeliveryFact) -> None:
        self.runs += delivery.team_runs
        if delivery.is_legal:
            self.legal_balls += 1
        if delivery.striker_id == self.batter_1_id:
            self.batter_1_runs += delivery.runs_off_bat
        elif delivery.striker_id == self.batter_2_id:
            self.batter_2_runs += delivery.runs_off_bat

    def close(self, *, end_score: int, is_current: bool) -> PartnershipFact:
        return PartnershipFact(
            batter_1_id=self.batter_1_id,
            batter_2_id=self.batter_2_id,
            runs=self.runs,
            legal_balls=self.legal_balls,
            start_score=self.start_score,
            end_score=end_score,
            is_current=is_current,
            batter_1_runs=self.batter_1_runs,
            batter_2_runs=self.batter_2_runs,
        )


def _order_pair(
    striker_id: UUID,
    non_striker_id: UUID,
    previous: frozenset[UUID] | None,
) -> tuple[UUID, UUID]:
    incoming = frozenset({striker_id, non_striker_id})
    if previous is not None:
        continuing = incoming & previous
        if len(continuing) == 1:
            first = next(iter(continuing))
            second = next(iter(incoming - continuing))
            return first, second
    return striker_id, non_striker_id


def build_partnerships(
    deliveries: Sequence[DeliveryFact],
    *,
    innings_complete: bool,
    opening: tuple[UUID, UUID] | None = None,
) -> list[PartnershipFact]:
    if not deliveries:
        if opening is None:
            return []
        return [
            PartnershipFact(
                batter_1_id=opening[0],
                batter_2_id=opening[1],
                runs=0,
                legal_balls=0,
                start_score=0,
                end_score=0,
                is_current=not innings_complete,
                batter_1_runs=0,
                batter_2_runs=0,
            )
        ]

    partnerships: list[PartnershipFact] = []
    current: _OpenPartnership | None = None
    score = 0
    previous_pair: frozenset[UUID] | None = None

    for delivery in deliveries:
        pair = frozenset({delivery.striker_id, delivery.non_striker_id})
        if current is None or current.pair != pair:
            if current is not None:
                partnerships.append(current.close(end_score=score, is_current=False))
                previous_pair = current.pair
            first, second = _order_pair(delivery.striker_id, delivery.non_striker_id, previous_pair)
            current = _OpenPartnership(batter_1_id=first, batter_2_id=second, start_score=score)
        current.add(delivery)
        score += delivery.team_runs
        if delivery.is_team_wicket:
            partnerships.append(current.close(end_score=score, is_current=False))
            previous_pair = current.pair
            current = None

    if current is not None:
        partnerships.append(current.close(end_score=score, is_current=not innings_complete))
    return partnerships
