from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

Importance = Literal["HIGH", "MEDIUM", "LOW"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]


class AnalysisSection(BaseModel):
    title: str = Field(max_length=80)
    insight: str = Field(max_length=400)
    fact_ids: list[str] = Field(min_length=1, max_length=8)
    importance: Importance = "MEDIUM"
    match_player_id: uuid.UUID | None = None
    match_team_id: uuid.UUID | None = None
    event_type: str | None = None


class PlayerOfMatchRecommendation(BaseModel):
    match_player_id: uuid.UUID
    reason: str = Field(max_length=400)
    confidence: Confidence
    fact_ids: list[str] = Field(min_length=1, max_length=8)


class StructuredMatchAnalysis(BaseModel):
    headline: str = Field(max_length=120)
    summary: str = Field(max_length=1800)
    winning_factors: list[AnalysisSection] = Field(max_length=5)
    losing_factors: list[AnalysisSection] = Field(max_length=5)
    batting_analysis: list[AnalysisSection] = Field(max_length=6)
    bowling_analysis: list[AnalysisSection] = Field(max_length=6)
    partnership_analysis: list[AnalysisSection] = Field(max_length=4)
    phase_analysis: list[AnalysisSection] = Field(max_length=6)
    turning_points: list[AnalysisSection] = Field(max_length=5)
    key_moments: list[AnalysisSection] = Field(max_length=5)
    tactical_observations: list[AnalysisSection] = Field(max_length=5)
    recommendations: list[AnalysisSection] = Field(max_length=5)
    player_of_match: PlayerOfMatchRecommendation
    winning_match_team_id: uuid.UUID | None = None
