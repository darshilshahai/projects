from numbers import Number

from app.core.exceptions import ChartValidationError
from app.schemas.chart import ChartRequest


class ChartValidator:
    MAX_PIE_CATEGORIES = 8

    def validate(
        self,
        *,
        request: ChartRequest,
        rows: list[dict],
        columns: list[str],
    ) -> None:
        if not rows:
            raise ChartValidationError(
                "A chart cannot be created because the query returned no rows."
            )

        self._validate_columns(
            request=request,
            columns=columns,
        )

        self._validate_y_values(
            request=request,
            rows=rows,
        )

        self._validate_scatter(
            request=request,
            rows=rows,
        )

        self._validate_pie(
            request=request,
            rows=rows,
        )

    def _validate_columns(
        self,
        *,
        request: ChartRequest,
        columns: list[str],
    ) -> None:
        if request.x not in columns:
            raise ChartValidationError(
                f"Chart x column '{request.x}' "
                "was not returned by the SQL query."
            )

        if request.y not in columns:
            raise ChartValidationError(
                f"Chart y column '{request.y}' "
                "was not returned by the SQL query."
            )

        if request.x == request.y:
            raise ChartValidationError(
                "Chart x and y columns must be different."
            )

    def _validate_y_values(
        self,
        *,
        request: ChartRequest,
        rows: list[dict],
    ) -> None:
        numeric_values = [
            row.get(request.y)
            for row in rows
            if row.get(request.y) is not None
        ]

        if not numeric_values:
            raise ChartValidationError(
                f"Chart y column '{request.y}' contains no values."
            )

        if not all(
            isinstance(value, Number)
            and not isinstance(value, bool)
            for value in numeric_values
        ):
            raise ChartValidationError(
                f"Chart y column '{request.y}' "
                "must contain numeric values."
            )

    def _validate_scatter(
        self,
        *,
        request: ChartRequest,
        rows: list[dict],
    ) -> None:
        if request.chart_type != "scatter":
            return

        x_values = [
            row.get(request.x)
            for row in rows
            if row.get(request.x) is not None
        ]

        if not x_values:
            raise ChartValidationError(
                "Scatter chart x-axis has no values."
            )

        if not all(
            isinstance(value, Number)
            and not isinstance(value, bool)
            for value in x_values
        ):
            raise ChartValidationError(
                "Scatter charts require a numeric x-axis."
            )

    def _validate_pie(
        self,
        *,
        request: ChartRequest,
        rows: list[dict],
    ) -> None:
        if request.chart_type != "pie":
            return

        if len(rows) > self.MAX_PIE_CATEGORIES:
            raise ChartValidationError(
                "Pie charts are limited to 8 categories. "
                "Use a bar chart for larger categorical comparisons."
            )

        values = [
            row.get(request.y)
            for row in rows
            if row.get(request.y) is not None
        ]

        if any(value < 0 for value in values):
            raise ChartValidationError(
                "Pie charts cannot represent negative values."
            )

        if sum(values) <= 0:
            raise ChartValidationError(
                "Pie chart values must have a positive total."
            )