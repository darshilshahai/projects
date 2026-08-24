from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisEvidence(BaseModel):
    fact_id: str
    type: str
    label: str
    summary: str


class AnalysisPointOut(BaseModel):
    title: str
    insight: str
    importance: str
    evidence: list[AnalysisEvidence] = Field(default_factory=list)
    match_player_id: uuid.UUID | None = None
    match_player_name: str | None = None
    match_team_id: uuid.UUID | None = None
    match_team_name: str | None = None
    event_type: str | None = None


class PlayerOfMatchOut(BaseModel):
    match_player_id: uuid.UUID
    name: str
    reason: str
    confidence: str
    evidence: list[AnalysisEvidence] = Field(default_factory=list)
    is_recommendation: bool = True


class MatchAnalysisBody(BaseModel):
    headline: str
    summary: str
    winning_factors: list[AnalysisPointOut] = Field(default_factory=list)
    losing_factors: list[AnalysisPointOut] = Field(default_factory=list)
    batting_analysis: list[AnalysisPointOut] = Field(default_factory=list)
    bowling_analysis: list[AnalysisPointOut] = Field(default_factory=list)
    partnership_analysis: list[AnalysisPointOut] = Field(default_factory=list)
    phase_analysis: list[AnalysisPointOut] = Field(default_factory=list)
    turning_points: list[AnalysisPointOut] = Field(default_factory=list)
    key_moments: list[AnalysisPointOut] = Field(default_factory=list)
    tactical_observations: list[AnalysisPointOut] = Field(default_factory=list)
    recommendations: list[AnalysisPointOut] = Field(default_factory=list)
    player_of_match: PlayerOfMatchOut


class AnalysisMetadata(BaseModel):
    generated_at: datetime
    provider: str
    model: str
    analysis_version: str
    prompt_version: str
    facts_version: str


class MatchAnalysisResponse(BaseModel):
    analysis: MatchAnalysisBody
    metadata: AnalysisMetadata
