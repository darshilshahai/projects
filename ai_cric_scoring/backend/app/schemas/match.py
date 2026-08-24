from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.cricket.types import ResultType
from app.models.enums import MatchFormat, MatchSide, MatchStatus, PlayerRole, TossDecision


class MatchListScope(StrEnum):
    ACTIVE = "active"
    HISTORY = "history"


class MatchCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    format: MatchFormat
    overs_per_innings: int | None = Field(default=None, ge=1, le=50)
    balls_per_over: int = Field(default=6, ge=1, le=10)
    venue_name: str | None = Field(default=None, max_length=200)
    scheduled_at: datetime | None = None
    players_per_team: int = Field(default=11, ge=2, le=11)

    @field_validator("name", "venue_name")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = " ".join(value.split())
        return stripped or None


class MatchUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    format: MatchFormat | None = None
    overs_per_innings: int | None = Field(default=None, ge=1, le=50)
    balls_per_over: int | None = Field(default=None, ge=1, le=10)
    venue_name: str | None = Field(default=None, max_length=200)
    scheduled_at: datetime | None = None
    players_per_team: int | None = Field(default=None, ge=2, le=11)

    @field_validator("name", "venue_name")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = " ".join(value.split())
        return stripped or None


class MatchTeamsRequest(BaseModel):
    team_a_id: uuid.UUID
    team_b_id: uuid.UUID


class PlayingXiPlayerRequest(BaseModel):
    player_id: uuid.UUID
    is_captain: bool = False
    is_wicket_keeper: bool = False
    batting_position: int | None = Field(default=None, ge=1, le=11)


class PlayingXiTeamRequest(BaseModel):
    match_team_id: uuid.UUID
    players: list[PlayingXiPlayerRequest]


class PlayingXiRequest(BaseModel):
    teams: list[PlayingXiTeamRequest] = Field(min_length=1, max_length=2)


class TossRequest(BaseModel):
    winner_match_team_id: uuid.UUID
    decision: TossDecision


class MatchPlayerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    player_id: uuid.UUID
    name: str
    is_playing: bool
    is_captain: bool
    is_wicket_keeper: bool
    batting_position: int | None
    player_role: PlayerRole | None = None


class MatchTeamPublic(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    side: MatchSide
    name: str
    short_name: str | None
    players: list[MatchPlayerPublic] = Field(default_factory=list)


class TossPublic(BaseModel):
    winner_match_team_id: uuid.UUID
    decision: TossDecision


class MatchResultPublic(BaseModel):
    result_type: ResultType | None = None
    winner_match_team_id: uuid.UUID | None = None
    winner_name: str | None = None
    margin_runs: int | None = None
    margin_wickets: int | None = None
    summary: str | None = None


class TeamScoreSummary(BaseModel):
    match_team_id: uuid.UUID
    name: str
    short_name: str | None = None
    runs: int
    wickets: int
    legal_balls: int
    overs: str
    all_out: bool = False


class InningsSummaryPublic(BaseModel):
    number: int
    batting_match_team_id: uuid.UUID
    batting_team_name: str
    runs: int
    wickets: int
    legal_balls: int
    overs: str
    all_out: bool = False


class MatchSummary(BaseModel):
    id: uuid.UUID
    name: str | None
    format: MatchFormat
    status: MatchStatus
    venue_name: str | None
    scheduled_at: datetime | None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    overs_per_innings: int
    balls_per_over: int
    players_per_team: int
    team_a_name: str | None = None
    team_b_name: str | None = None
    team_a_score: TeamScoreSummary | None = None
    team_b_score: TeamScoreSummary | None = None
    result: MatchResultPublic | None = None
    created_at: datetime
    updated_at: datetime


class MatchListResponse(BaseModel):
    items: list[MatchSummary]
    total: int
    limit: int
    offset: int


class MatchDetailResponse(BaseModel):
    id: uuid.UUID
    name: str | None
    format: MatchFormat
    status: MatchStatus
    venue_name: str | None
    scheduled_at: datetime | None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    overs_per_innings: int
    balls_per_over: int
    players_per_team: int
    created_at: datetime
    updated_at: datetime
    teams: list[MatchTeamPublic]
    toss: TossPublic | None = None
    result: MatchResultPublic | None = None
    innings: list[InningsSummaryPublic] = Field(default_factory=list)
    readiness_issues: list[str] = Field(default_factory=list)
