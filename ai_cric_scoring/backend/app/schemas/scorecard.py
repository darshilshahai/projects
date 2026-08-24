from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.cricket.types import InningsStatus, ResultType
from app.models.enums import MatchFormat, MatchStatus


class ScorecardTeam(BaseModel):
    match_team_id: uuid.UUID
    name: str
    short_name: str | None = None


class ScorecardMatchHeader(BaseModel):
    id: uuid.UUID
    name: str | None
    format: MatchFormat
    status: MatchStatus
    venue_name: str | None
    overs_per_innings: int
    balls_per_over: int
    players_per_team: int
    team_a: ScorecardTeam | None = None
    team_b: ScorecardTeam | None = None
    result_type: ResultType | None = None
    winner_match_team_id: uuid.UUID | None = None
    winner_name: str | None = None
    margin_runs: int | None = None
    margin_wickets: int | None = None


class BattingScorecardRow(BaseModel):
    match_player_id: uuid.UUID
    name: str
    batting_position: int
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: float
    status: str
    dismissal_text: str
    is_striker: bool = False
    is_non_striker: bool = False


class YetToBatRow(BaseModel):
    match_player_id: uuid.UUID
    name: str


class BowlingScorecardRow(BaseModel):
    match_player_id: uuid.UUID
    name: str
    legal_balls: int
    overs: str
    maidens: int
    runs_conceded: int
    wickets: int
    economy: float
    wides: int
    no_balls: int


class ExtrasScorecard(BaseModel):
    total: int
    wides: int
    no_balls: int
    byes: int
    leg_byes: int
    penalty_runs: int


class FallOfWicketRow(BaseModel):
    wicket_number: int
    score: int
    player_id: uuid.UUID
    player_name: str
    legal_balls: int
    overs: str


class PartnershipRow(BaseModel):
    batter_1_id: uuid.UUID
    batter_1_name: str
    batter_2_id: uuid.UUID
    batter_2_name: str
    runs: int
    legal_balls: int
    start_score: int
    end_score: int
    is_current: bool
    batter_1_runs: int
    batter_2_runs: int


class OverDeliveryRow(BaseModel):
    label: str
    runs: int
    wicket: bool
    legal: bool


class OverSummaryRow(BaseModel):
    over_number: int
    runs: int
    wickets: int
    legal_balls: int
    is_complete: bool
    deliveries: list[OverDeliveryRow] = Field(default_factory=list)


class NamedScorecardStat(BaseModel):
    match_player_id: uuid.UUID
    name: str
    value: int


class MatchScorecardSummary(BaseModel):
    highest_scorers: list[NamedScorecardStat] = Field(default_factory=list)
    most_wickets: list[NamedScorecardStat] = Field(default_factory=list)
    total_boundaries: int = 0
    total_sixes: int = 0
    total_extras: int = 0
    largest_partnerships: list[NamedScorecardStat] = Field(default_factory=list)


class InningsScorecard(BaseModel):
    id: uuid.UUID
    number: int
    status: InningsStatus
    batting_team: ScorecardTeam
    bowling_team: ScorecardTeam
    runs: int
    wickets: int
    legal_balls: int
    overs: str
    run_rate: float
    required_run_rate: float | None = None
    target: int | None = None
    all_out: bool = False
    extras: ExtrasScorecard
    batting: list[BattingScorecardRow] = Field(default_factory=list)
    yet_to_bat: list[YetToBatRow] = Field(default_factory=list)
    bowling: list[BowlingScorecardRow] = Field(default_factory=list)
    fall_of_wickets: list[FallOfWicketRow] = Field(default_factory=list)
    partnerships: list[PartnershipRow] = Field(default_factory=list)
    overs_summary: list[OverSummaryRow] = Field(default_factory=list)


class MatchScorecardResponse(BaseModel):
    match: ScorecardMatchHeader
    status: MatchStatus
    current_innings_number: int | None = None
    innings: list[InningsScorecard] = Field(default_factory=list)
    summary: MatchScorecardSummary = Field(default_factory=MatchScorecardSummary)
