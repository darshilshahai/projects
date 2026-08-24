from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ExpectedAction = Literal[
    "answer",
    "chart",
    "clarification",
]


class ExpectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: str
    value: Any


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    question: str

    expected_action: ExpectedAction

    expected_chart_type: (
        Literal[
            "bar",
            "line",
            "pie",
            "scatter",
        ]
        | None
    ) = None

    expected_values: list[
        ExpectedCell
    ] = Field(
        default_factory=list
    )


class EvaluationCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    question: str

    expected_action: str
    actual_action: str

    action_pass: bool
    values_pass: bool
    chart_pass: bool

    passed: bool

    latency_ms: float

    input_tokens: int
    output_tokens: int
    total_tokens: int

    estimated_cost_usd: float

    sql: str | None = None
    failure_reason: str | None = None


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cases: int

    passed_cases: int
    failed_cases: int

    pass_rate: float

    action_accuracy: float
    value_accuracy: float
    chart_accuracy: float

    average_latency_ms: float
    p95_latency_ms: float

    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int

    total_estimated_cost_usd: float
    average_cost_usd: float


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: EvaluationSummary

    cases: list[
        EvaluationCaseResult
    ]