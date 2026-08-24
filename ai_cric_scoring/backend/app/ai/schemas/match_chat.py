from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionType(StrEnum):
    DIRECT_STAT = "DIRECT_STAT"
    PLAYER_PERFORMANCE = "PLAYER_PERFORMANCE"
    TEAM_PERFORMANCE = "TEAM_PERFORMANCE"
    COMPARISON = "COMPARISON"
    PARTNERSHIP = "PARTNERSHIP"
    BOWLING = "BOWLING"
    BATTING = "BATTING"
    EXTRAS = "EXTRAS"
    OVER_RANGE = "OVER_RANGE"
    TURNING_POINT = "TURNING_POINT"
    WHY_RESULT = "WHY_RESULT"
    MATCH_SUMMARY = "MATCH_SUMMARY"
    FIELDING = "FIELDING"
    UNKNOWN = "UNKNOWN"


class AnswerType(StrEnum):
    DIRECT_STAT = "DIRECT_STAT"
    ANALYTICAL = "ANALYTICAL"
    CLARIFICATION = "CLARIFICATION"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ContextMode(StrEnum):
    RESULT_ONLY = "RESULT_ONLY"
    PLAYER_BATTING = "PLAYER_BATTING"
    PLAYER_BOWLING = "PLAYER_BOWLING"
    PLAYER_FULL = "PLAYER_FULL"
    TEAM_INNINGS = "TEAM_INNINGS"
    PARTNERSHIPS = "PARTNERSHIPS"
    OVER_RANGE = "OVER_RANGE"
    COMPARISON = "COMPARISON"
    EXTRAS = "EXTRAS"
    FIELDING = "FIELDING"
    FULL_ANALYTICAL = "FULL_ANALYTICAL"
    NONE = "NONE"


class QuestionIntent(BaseModel):
    type: QuestionType
    requires_llm: bool = False
    answer_type: AnswerType = AnswerType.DIRECT_STAT
    player_names: list[str] = Field(default_factory=list)
    team_names: list[str] = Field(default_factory=list)
    over_start: int | None = None
    over_end: int | None = None
    last_n_overs: int | None = None
    innings_hint: int | None = None
    wants_chase: bool = False
    unavailable_topic: str | None = None
    out_of_scope: bool = False
    context_mode: ContextMode = ContextMode.RESULT_ONLY


class StructuredChatAnswer(BaseModel):
    content: str = Field(max_length=1200)
    fact_ids: list[str] = Field(default_factory=list, max_length=8)
    answer_type: Literal["ANALYTICAL"] = "ANALYTICAL"
    match_player_ids: list[UUID] = Field(default_factory=list, max_length=4)
    match_team_ids: list[UUID] = Field(default_factory=list, max_length=2)
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
