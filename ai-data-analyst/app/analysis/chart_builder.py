import json
from typing import Any

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder

from app.analysis.chart_validator import ChartValidator
from app.schemas.chart import ChartData, ChartRequest


class PlotlyChartBuilder:
    def __init__(
        self,
        validator: ChartValidator,
    ) -> None:
        self._validator = validator

    def build(
        self,
        *,
        request: ChartRequest,
        rows: list[dict[str, Any]],
        columns: list[str],
    ) -> ChartData:
        self._validator.validate(
            request=request,
            rows=rows,
            columns=columns,
        )

        dataframe = pd.DataFrame(rows)

        figure = self._create_figure(
            request=request,
            dataframe=dataframe,
        )

        self._apply_layout(
            figure=figure,
            request=request,
        )

        return ChartData(
            chart_type=request.chart_type,
            title=request.title,
            x=request.x,
            y=request.y,
            x_label=request.x_label,
            y_label=request.y_label,
            figure=json.loads(
                json.dumps(
                    figure.to_plotly_json(),
                    cls=PlotlyJSONEncoder,
                )
            ),
        )

    def _create_figure(
        self,
        *,
        request: ChartRequest,
        dataframe: pd.DataFrame,
    ) -> Figure:
        labels = {
            request.x: (request.x_label or self._humanize(request.x)),
            request.y: (request.y_label or self._humanize(request.y)),
        }

        if request.chart_type == "bar":
            return px.bar(
                dataframe,
                x=request.x,
                y=request.y,
                title=request.title,
                labels=labels,
            )

        if request.chart_type == "line":
            return px.line(
                dataframe,
                x=request.x,
                y=request.y,
                title=request.title,
                labels=labels,
                markers=True,
            )

        if request.chart_type == "pie":
            return px.pie(
                dataframe,
                names=request.x,
                values=request.y,
                title=request.title,
            )

        if request.chart_type == "scatter":
            return px.scatter(
                dataframe,
                x=request.x,
                y=request.y,
                title=request.title,
                labels=labels,
            )

        raise ValueError(f"Unsupported chart type: {request.chart_type}")

    def _apply_layout(
        self,
        *,
        figure: Figure,
        request: ChartRequest,
    ) -> None:
        figure.update_layout(
            template="plotly_dark",
            autosize=True,
            margin={
                "l": 50,
                "r": 30,
                "t": 70,
                "b": 50,
            },
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={
                "family": "Inter, Arial, sans-serif",
            },
            hoverlabel={
                "namelength": -1,
            },
        )

        if request.chart_type != "pie":
            figure.update_xaxes(
                showgrid=False,
                zeroline=False,
            )

            figure.update_yaxes(
                gridcolor="rgba(255,255,255,0.08)",
                zeroline=False,
            )

    @staticmethod
    def _humanize(value: str) -> str:
        return value.replace("_", " ").strip().title()
