from typing import ClassVar

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.core.exceptions import SQLValidationError


class SQLValidator:
    BLOCKED_FUNCTIONS: ClassVar[set[str]] = {
        "read_csv",
        "read_csv_auto",
        "read_json",
        "read_json_auto",
        "read_ndjson",
        "read_parquet",
        "parquet_scan",
        "csv_scan",
        "glob",
        "http_get",
        "getenv",
    }

    ALLOWED_BASE_TABLES: ClassVar[set[str]] = {
        "dataset",
    }

    def __init__(self, max_rows: int) -> None:
        self._max_rows = max_rows

    def validate_and_prepare(self, sql: str) -> str:
        sql = sql.strip()

        if not sql:
            raise SQLValidationError(
                "Generated SQL query is empty."
            )

        try:
            statements = parse(sql, read="duckdb")
        except ParseError as exc:
            raise SQLValidationError(
                f"Generated SQL could not be parsed: {exc}"
            ) from exc

        if len(statements) != 1:
            raise SQLValidationError(
                "Only one SQL statement may be executed."
            )

        expression = statements[0]

        self._validate_statement_type(expression)
        self._validate_tables(expression)
        self._validate_functions(expression)

        expression = self._apply_result_limit(expression)

        return expression.sql(dialect="duckdb")

    def _validate_statement_type(
        self,
        expression: exp.Expression,
    ) -> None:
        prohibited_nodes = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Create,
            exp.Drop,
            exp.Alter,
            exp.Command,
            exp.Copy,
            exp.Merge,
        )

        for node_type in prohibited_nodes:
            if expression.find(node_type):
                raise SQLValidationError(
                    "Only read-only analytical queries are allowed."
                )

        if not isinstance(
            expression,
            (
                exp.Select,
                exp.Union,
                exp.Intersect,
                exp.Except,
            ),
        ):
            raise SQLValidationError(
                "Only SELECT-style analytical queries are allowed."
            )

    def _validate_tables(
        self,
        expression: exp.Expression,
    ) -> None:
        cte_names = {
            cte.alias_or_name.lower()
            for cte in expression.find_all(exp.CTE)
            if cte.alias_or_name
        }

        allowed_tables = self.ALLOWED_BASE_TABLES | cte_names

        for table in expression.find_all(exp.Table):
            table_name = table.name.lower()

            if table_name not in allowed_tables:
                raise SQLValidationError(
                    f"Table '{table.name}' is not allowed. "
                    "Only the uploaded dataset may be queried."
                )

            if table.db or table.catalog:
                raise SQLValidationError(
                    "Database-qualified table names are not allowed."
                )

    def _validate_functions(
        self,
        expression: exp.Expression,
    ) -> None:
        for function in expression.find_all(exp.Func):
            function_name = function.sql_name().lower()

            if function_name in self.BLOCKED_FUNCTIONS:
                raise SQLValidationError(
                    f"Function '{function_name}' is not allowed."
                )

    def _apply_result_limit(
        self,
        expression: exp.Expression,
    ) -> exp.Expression:
        current_limit = expression.args.get("limit")

        if current_limit is None:
            return expression.limit(self._max_rows)

        limit_expression = current_limit.expression

        if isinstance(limit_expression, exp.Literal):
            try:
                requested_limit = int(limit_expression.this)
            except ValueError:
                requested_limit = self._max_rows

            if requested_limit > self._max_rows:
                expression.set(
                    "limit",
                    exp.Limit(
                        expression=exp.Literal.number(
                            self._max_rows
                        )
                    ),
                )

        return expression