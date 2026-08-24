from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    BUILD = "BUILD"
    MODIFY = "MODIFY"
    KILL = "KILL"


class MarketSaturation(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DifferentiationStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class Competitor(BaseModel):
    name: str
    description: str
    url: str | None = None


class Differentiation(BaseModel):
    description: str
    strength: DifferentiationStrength


class MVPRecommendation(BaseModel):
    target_user: str
    core_problem: str
    core_feature: str
    avoid_features: list[str] = Field(min_length=1, max_length=5)


class Scores(BaseModel):
    problem_clarity: int = Field(ge=0, le=100)
    differentiation: int = Field(ge=0, le=100)
    opportunity: int = Field(ge=0, le=100)


class AnalyzeResponse(BaseModel):
    idea_summary: str
    target_user: str
    problem: str
    market_saturation: MarketSaturation
    competitors: list[Competitor]
    biggest_problem: str
    differentiation: Differentiation
    recommended_wedge: str
    mvp: MVPRecommendation
    scores: Scores
    verdict: Verdict
    confidence: int = Field(ge=0, le=100)
    reason: str


class IdeaAnalysisOutput(BaseModel):
    idea_summary: str
    target_user: str
    problem: str
    market_saturation: MarketSaturation
    biggest_problem: str
    differentiation: Differentiation
    recommended_wedge: str
    mvp: MVPRecommendation
    scores: Scores
    verdict: Verdict
    confidence: int = Field(ge=0, le=100)
    reason: str
