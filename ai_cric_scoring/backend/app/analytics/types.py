from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.cricket.types import DismissalType


@dataclass(frozen=True)
class DeliveryFact:
    sequence_number: int
    over_number: int
    striker_id: UUID
    non_striker_id: UUID
    bowler_id: UUID
    runs_off_bat: int
    wides: int
    no_balls: int
    byes: int
    leg_byes: int
    penalty_runs: int
    is_legal: bool
    dismissal_type: DismissalType | None = None
    dismissed_player_id: UUID | None = None
    fielder_id: UUID | None = None
    credited_to_bowler: bool = False

    @property
    def team_runs(self) -> int:
        return self.runs_off_bat + self.wides + self.no_balls + self.byes + self.leg_byes + self.penalty_runs

    @property
    def bowler_runs(self) -> int:
        return self.runs_off_bat + self.wides + self.no_balls

    @property
    def is_team_wicket(self) -> bool:
        return self.dismissal_type is not None


@dataclass(frozen=True)
class ExtrasBreakdown:
    wides: int
    no_balls: int
    byes: int
    leg_byes: int
    penalty_runs: int

    @property
    def total(self) -> int:
        return self.wides + self.no_balls + self.byes + self.leg_byes + self.penalty_runs

    @property
    def non_bowler_charged(self) -> int:
        return self.byes + self.leg_byes + self.penalty_runs


@dataclass(frozen=True)
class OverDeliveryFact:
    label: str
    runs: int
    wicket: bool
    legal: bool


@dataclass(frozen=True)
class OverSummaryFact:
    over_number: int
    runs: int
    wickets: int
    legal_balls: int
    is_complete: bool
    deliveries: tuple[OverDeliveryFact, ...]


@dataclass(frozen=True)
class PartnershipFact:
    batter_1_id: UUID
    batter_2_id: UUID
    runs: int
    legal_balls: int
    start_score: int
    end_score: int
    is_current: bool
    batter_1_runs: int
    batter_2_runs: int


@dataclass(frozen=True)
class NamedStat:
    match_player_id: UUID
    name: str
    value: int


@dataclass(frozen=True)
class MatchSummaryFacts:
    highest_scorers: tuple[NamedStat, ...]
    most_wickets: tuple[NamedStat, ...]
    total_boundaries: int
    total_sixes: int
    total_extras: int
    largest_partnerships: tuple[NamedStat, ...]
