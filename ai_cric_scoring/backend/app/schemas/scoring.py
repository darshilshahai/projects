from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.cricket.types import DismissalType, InningsStatus, ResultType
from app.models.enums import MatchStatus


class StartMatchRequest(BaseModel):
    striker_id: uuid.UUID
    non_striker_id: uuid.UUID
    bowler_id: uuid.UUID
    client_event_id: uuid.UUID


class SelectPlayerRequest(BaseModel):
    client_event_id: uuid.UUID
    base_revision: int = Field(ge=0)
    player_id: uuid.UUID


class UndoRequest(BaseModel):
    client_event_id: uuid.UUID
    base_revision: int = Field(ge=0)


class DismissalPayload(BaseModel):
    type: DismissalType
    dismissed_player_id: uuid.UUID | None = None
    fielder_id: uuid.UUID | None = None
    crossed: bool = False


class DeliveryPayload(BaseModel):
    runs_off_bat: int = 0
    wides: int = 0
    no_balls: int = 0
    byes: int = 0
    leg_byes: int = 0
    penalty_runs: int = 0
    dismissal: DismissalPayload | None = None


class RetirePayload(BaseModel):
    player_id: uuid.UUID | None = None
    hurt: bool = True


class ScoringEventRequest(BaseModel):
    client_event_id: uuid.UUID
    base_revision: int = Field(ge=0)
    type: Literal["DELIVERY", "RETIRE"] = "DELIVERY"
    delivery: DeliveryPayload | None = None
    retire: RetirePayload | None = None


class LiveTeam(BaseModel):
    match_team_id: uuid.UUID
    name: str


class LiveBatterCard(BaseModel):
    match_player_id: uuid.UUID
    name: str
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: float | None
    is_striker: bool


class LiveBowlerCard(BaseModel):
    match_player_id: uuid.UUID
    name: str
    overs: str
    legal_balls: int
    runs: int
    wickets: int
    economy: float | None
    wides: int
    no_balls: int


class CurrentOverBall(BaseModel):
    label: str
    runs: int
    wicket: bool
    legal: bool


class LiveBatterOption(BaseModel):
    match_player_id: uuid.UUID
    name: str
    selectable: bool
    status: str
    runs: int = 0
    balls: int = 0


class LiveBowlerOption(BaseModel):
    match_player_id: uuid.UUID
    name: str
    selectable: bool
    unavailable_reason: str | None = None
    overs: str
    legal_balls: int
    runs: int
    wickets: int
    economy: float | None


class LiveInnings(BaseModel):
    id: uuid.UUID
    number: int
    status: InningsStatus
    batting_team: LiveTeam
    bowling_team: LiveTeam
    runs: int
    wickets: int
    legal_balls: int
    overs: str
    balls_remaining: int | None = None
    current_run_rate: float | None
    target: int | None
    required_runs: int | None
    required_run_rate: float | None


class LiveMatchState(BaseModel):
    match_id: uuid.UUID
    status: MatchStatus
    revision: int
    innings: LiveInnings | None = None
    striker: LiveBatterCard | None = None
    non_striker: LiveBatterCard | None = None
    bowler: LiveBowlerCard | None = None
    current_over: list[CurrentOverBall] = Field(default_factory=list)
    needs_new_batter: bool = False
    needs_new_bowler: bool = False
    needs_openers: bool = False
    pending_innings_id: uuid.UUID | None = None
    chase_target: int | None = None
    available_batters: list[LiveBatterOption] = Field(default_factory=list)
    available_bowlers: list[LiveBowlerOption] = Field(default_factory=list)
    result_type: ResultType | None = None
    winner_match_team_id: uuid.UUID | None = None
    margin_runs: int | None = None
    margin_wickets: int | None = None
    idempotent: bool = False


class ScoringEventPublic(BaseModel):
    id: uuid.UUID
    sequence_number: int
    event_type: str
    client_event_id: uuid.UUID | None
    is_voided: bool
    payload: dict[str, Any]
    created_by_user_id: uuid.UUID
    created_at: str


class ScoringEventListResponse(BaseModel):
    items: list[ScoringEventPublic]
    revision: int
