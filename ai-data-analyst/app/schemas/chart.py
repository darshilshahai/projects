from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ChartType = Literal[
    "bar",
    "line",
    "pie",
    "scatter",
]

class ChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_type: ChartType
    x: str = Field(min_length=1)
    y: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    x_label: str | None = None
    y_label: str | None = None


class ChartData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_type: ChartType
    title: str

    x: str
    y: str

    x_label: str | None = None
    y_label: str | None = None

    figure: dict[str, Any]