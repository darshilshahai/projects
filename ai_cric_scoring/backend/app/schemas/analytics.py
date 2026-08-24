from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.analytics.history.definitions import LAST_N_MAX, LAST_N_MIN
from app.models.enums import MatchFormat

LeaderboardMetric = Literal["runs", "wickets", "batting_average", "strike_rate", "economy"]


class HistoricalScopeIn(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    format: MatchFormat | None = None
    team_id: UUID | None = None
    last_n: int | None = Field(default=None, ge=LAST_N_MIN, le=LAST_N_MAX)


class HistoricalScopeOut(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    format: MatchFormat | None = None
    team_id: UUID | None = None
    last_n: int | None = None
    completed_only: bool = True
    description: str


class BattingCareerOut(BaseModel):
    matches: int
    innings: int
    runs: int
    balls: int
    not_outs: int
    dismissals: int
    highest_score: int | None = None
    highest_score_display: str | None = None
    fours: int
    sixes: int
    strike_rate: float | None = None
    batting_average: float | None = None


class BowlingCareerOut(BaseModel):
    matches: int
    innings_bowled: int
    legal_balls: int
    overs_display: str | None = None
    runs_conceded: int
    wickets: int
    wides: int
    no_balls: int
    maidens: int
    economy: float | None = None
    bowling_average: float | None = None
    best_bowling: str | None = None
    mixed_rules: bool = False
    runs_per_legal_ball: float | None = None


class FormAppearanceOut(BaseModel):
    match_id: UUID
    completed_at: datetime | None = None
    opponent_name: str | None = None
    runs: int | None = None
    not_out: bool | None = None
    wickets: int | None = None
    display: str | None = None
    result: str | None = None


class PlayerAnalyticsResponse(BaseModel):
    player_id: UUID
    name: str
    is_active: bool
    scope: HistoricalScopeOut
    batting: BattingCareerOut
    bowling: BowlingCareerOut
    recent_form: list[FormAppearanceOut]
    small_sample: bool = False


class TeamAnalyticsResponse(BaseModel):
    team_id: UUID
    name: str
    is_active: bool
    scope: HistoricalScopeOut
    matches: int
    wins: int
    losses: int
    ties: int
    win_percentage: float | None = None
    average_runs_scored: float | None = None
    average_runs_conceded: float | None = None
    highest_score: int | None = None
    lowest_completed_score: int | None = None
    matches_chasing: int = 0
    wins_chasing: int = 0
    matches_defending: int = 0
    wins_defending: int = 0
    recent_form: list[str]
    recent_matches: list[FormAppearanceOut]
    small_sample: bool = False


class LeaderboardEntryOut(BaseModel):
    player_id: UUID
    name: str
    metric: str
    value: float
    innings: int | None = None
    matches: int | None = None
    sample_label: str | None = None


class LeaderboardResponse(BaseModel):
    metric: str
    scope: HistoricalScopeOut
    items: list[LeaderboardEntryOut]
    total: int
    limit: int
    offset: int
    qualification: str | None = None


class PlayerCompareRequest(BaseModel):
    player_a_id: UUID
    player_b_id: UUID
    scope: HistoricalScopeIn = Field(default_factory=HistoricalScopeIn)


class PlayerCompareResponse(BaseModel):
    scope: HistoricalScopeOut
    player_a: PlayerAnalyticsResponse
    player_b: PlayerAnalyticsResponse
    note: str | None = None


class TeamCompareRequest(BaseModel):
    team_a_id: UUID
    team_b_id: UUID
    scope: HistoricalScopeIn = Field(default_factory=HistoricalScopeIn)


class HeadToHeadOut(BaseModel):
    matches: int
    team_a_wins: int
    team_b_wins: int
    ties: int


class TeamCompareResponse(BaseModel):
    scope: HistoricalScopeOut
    team_a: TeamAnalyticsResponse
    team_b: TeamAnalyticsResponse
    head_to_head: HeadToHeadOut


class OverviewTeamForm(BaseModel):
    team_id: UUID
    name: str
    results: list[str]
    win_percentage: float | None = None
    matches: int


class AnalyticsOverviewResponse(BaseModel):
    completed_matches: int
    player_count: int
    team_count: int
    top_runs: LeaderboardEntryOut | None = None
    top_wickets: LeaderboardEntryOut | None = None
    team_form: OverviewTeamForm | None = None
    suggestions: list[str]


class HistoricalQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class HistoricalEvidence(BaseModel):
    fact_id: str
    type: str
    label: str
    summary: str


class HistoricalClarificationOption(BaseModel):
    label: str
    message: str


class HistoricalQueryResponse(BaseModel):
    content: str
    answer_type: str
    question_type: str | None = None
    scope: HistoricalScopeOut | None = None
    evidence: list[HistoricalEvidence] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    clarification_options: list[HistoricalClarificationOption] = Field(default_factory=list)
    used_ai: bool = False
    facts: dict | None = None
    generation_error: dict | None = None
