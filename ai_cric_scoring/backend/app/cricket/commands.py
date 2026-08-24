from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.cricket.types import DismissalType


@dataclass(frozen=True)
class DismissalCommand:
    type: DismissalType
    dismissed_player_id: UUID
    fielder_id: UUID | None = None
    crossed: bool = False


@dataclass(frozen=True)
class DeliveryCommand:
    runs_off_bat: int = 0
    wides: int = 0
    no_balls: int = 0
    byes: int = 0
    leg_byes: int = 0
    penalty_runs: int = 0
    dismissal: DismissalCommand | None = None

    @property
    def team_runs(self) -> int:
        return self.runs_off_bat + self.wides + self.no_balls + self.byes + self.leg_byes + self.penalty_runs

    @property
    def is_legal(self) -> bool:
        return self.wides == 0 and self.no_balls == 0

    def bowler_conceded(self, *, penalty_charged_to_bowler: bool) -> int:
        conceded = self.runs_off_bat + self.wides + self.no_balls
        if penalty_charged_to_bowler:
            conceded += self.penalty_runs
        return conceded

    def running_runs(self) -> int:
        if self.wides > 0:
            return self.wides - 1
        return self.runs_off_bat + self.byes + self.leg_byes


@dataclass(frozen=True)
class SelectBatterCommand:
    player_id: UUID


@dataclass(frozen=True)
class SelectBowlerCommand:
    player_id: UUID


@dataclass(frozen=True)
class RetireCommand:
    player_id: UUID
    hurt: bool = True
