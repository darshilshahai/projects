from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chart import ChartData


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(
        min_length=1,
    )

    question: str = Field(
        min_length=1,
        max_length=5000,
    )


class ClarificationOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(
        min_length=1,
        max_length=100,
    )

    value: str = Field(
        min_length=1,
        max_length=200,
    )


class AnalysisMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latency_ms: float = Field(
        ge=0,
    )

    llm_calls: int = Field(
        ge=0,
    )

    input_tokens: int = Field(
        ge=0,
    )

    cached_input_tokens: int = Field(
        ge=0,
    )

    output_tokens: int = Field(
        ge=0,
    )

    reasoning_tokens: int = Field(
        ge=0,
    )

    total_tokens: int = Field(
        ge=0,
    )

    estimated_cost_usd: float = Field(
        ge=0,
    )


class AnalysisAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["answer"] = "answer"

    question: str
    answer: str

    sql: str

    columns: list[str]

    rows: list[
        dict[str, Any]
    ]

    row_count: int = Field(
        ge=0,
    )

    chart: ChartData | None = None

    metrics: AnalysisMetrics


class AnalysisClarificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["clarification"] = "clarification"

    question: str

    clarification_question: str

    options: list[
        ClarificationOption
    ]

    metrics: AnalysisMetrics


AnalysisResponse = (
    AnalysisAnswerResponse
    | AnalysisClarificationResponse
)