from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.cricket.rules import MatchRules
from app.cricket.types import BatterStatus, DismissalType, InningsStatus, MatchPlayStatus, ResultType


@dataclass
class BatterState:
    player_id: UUID
    batting_position: int
    runs: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    is_out: bool = False
    dismissal_type: DismissalType | None = None
    is_retired_hurt: bool = False
    is_retired_out: bool = False

    @property
    def status(self) -> BatterStatus:
        if self.is_retired_out or (self.is_out and self.dismissal_type == DismissalType.RETIRED_OUT):
            return BatterStatus.RETIRED_OUT
        if self.is_retired_hurt and not self.is_out:
            return BatterStatus.RETIRED_HURT
        if self.is_out:
            return BatterStatus.OUT
        return BatterStatus.BATTING

    @property
    def strike_rate(self) -> float | None:
        if self.balls_faced == 0:
            return None
        return self.runs / self.balls_faced * 100


@dataclass
class BowlerState:
    player_id: UUID
    legal_balls: int = 0
    runs_conceded: int = 0
    wickets: int = 0
    wides: int = 0
    no_balls: int = 0
    maidens: int = 0
    current_over_conceded: int = 0

    @property
    def economy(self) -> float | None:
        return None


@dataclass
class PartnershipState:
    batter_1_id: UUID
    batter_2_id: UUID
    runs: int = 0
    legal_balls: int = 0
    start_score: int = 0


@dataclass
class FallOfWicket:
    wicket_number: int
    team_score: int
    player_id: UUID
    legal_balls: int


@dataclass
class OverBall:
    label: str
    runs: int
    wicket: bool
    legal: bool


@dataclass
class InningsState:
    innings_number: int
    batting_team_id: UUID
    bowling_team_id: UUID
    batting_player_ids: tuple[UUID, ...]
    bowling_player_ids: tuple[UUID, ...]
    status: InningsStatus = InningsStatus.LIVE
    total_runs: int = 0
    wickets: int = 0
    legal_balls: int = 0
    target_runs: int | None = None
    striker_id: UUID | None = None
    non_striker_id: UUID | None = None
    current_bowler_id: UUID | None = None
    previous_bowler_id: UUID | None = None
    needs_new_batter: bool = False
    needs_new_bowler: bool = False
    vacant_end: str | None = None
    next_batting_position: int = 3
    batters: dict[UUID, BatterState] = field(default_factory=dict)
    bowlers: dict[UUID, BowlerState] = field(default_factory=dict)
    current_partnership: PartnershipState | None = None
    fall_of_wickets: list[FallOfWicket] = field(default_factory=list)
    current_over: list[OverBall] = field(default_factory=list)

    @property
    def is_live(self) -> bool:
        return self.status == InningsStatus.LIVE


@dataclass
class MatchState:
    match_id: UUID
    rules: MatchRules
    batting_first_team_id: UUID
    bowling_first_team_id: UUID
    status: MatchPlayStatus = MatchPlayStatus.LIVE
    innings: list[InningsState] = field(default_factory=list)
    winner_team_id: UUID | None = None
    result_type: ResultType | None = None
    margin_runs: int | None = None
    margin_wickets: int | None = None

    @property
    def current_innings(self) -> InningsState | None:
        live = [item for item in self.innings if item.status == InningsStatus.LIVE]
        if live:
            return live[-1]
        return self.innings[-1] if self.innings else None
