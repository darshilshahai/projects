from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import MatchFormat


class HistoricalQuestionType(StrEnum):
    PLAYER_STATS = "PLAYER_STATS"
    PLAYER_FORM = "PLAYER_FORM"
    PLAYER_COMPARISON = "PLAYER_COMPARISON"
    PLAYER_RANKING = "PLAYER_RANKING"
    TEAM_STATS = "TEAM_STATS"
    TEAM_FORM = "TEAM_FORM"
    TEAM_COMPARISON = "TEAM_COMPARISON"
    HEAD_TO_HEAD = "HEAD_TO_HEAD"
    HISTORICAL_TREND = "HISTORICAL_TREND"
    DIRECT_HISTORICAL_STAT = "DIRECT_HISTORICAL_STAT"
    UNKNOWN = "UNKNOWN"


class HistoricalAnswerType(StrEnum):
    DIRECT_STAT = "DIRECT_STAT"
    ANALYTICAL = "ANALYTICAL"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class HistoricalIntent(BaseModel):
    type: HistoricalQuestionType
    requires_llm: bool = False
    answer_type: HistoricalAnswerType = HistoricalAnswerType.DIRECT_STAT
    player_names: list[str] = Field(default_factory=list)
    team_names: list[str] = Field(default_factory=list)
    last_n: int | None = None
    format: MatchFormat | None = None
    ranking_metric: str | None = None
    season_clarification: bool = False
    out_of_scope: bool = False
    unavailable_topic: str | None = None


class StructuredHistoricalInsight(BaseModel):
    summary: str = Field(max_length=1200)
    insights: list[str] = Field(default_factory=list, max_length=6)
    fact_ids: list[str] = Field(default_factory=list, max_length=8)
    caveats: list[str] = Field(default_factory=list, max_length=4)
    player_ids: list[UUID] = Field(default_factory=list, max_length=4)
    team_ids: list[UUID] = Field(default_factory=list, max_length=2)
