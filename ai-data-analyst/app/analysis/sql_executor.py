from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from app.core.exceptions import SQLExecutionError
from app.datasets.profiler import DatasetProfiler
from app.utils.files import json_safe


class SQLExecutionResult:
    def __init__(
        self,
        *,
        sql: str,
        columns: list[str],
        rows: list[dict[str, Any]],
    ) -> None:
        self.sql = sql
        self.columns = columns
        self.rows = rows

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sql": self.sql,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
        }


class SQLExecutor:
    def __init__(
        self,
        profiler: DatasetProfiler,
    ) -> None:
        self._profiler = profiler

    def execute(
        self,
        *,
        csv_path: Path,
        sql: str,
    ) -> SQLExecutionResult:
        dataframe = self._profiler.load_csv(csv_path)

        connection = duckdb.connect(
            database=":memory:",
            config={
                "enable_external_access": "false",
            },
        )

        try:
            connection.register(
                "dataset",
                dataframe,
            )

            result = connection.execute(sql)

            result_dataframe: pd.DataFrame = result.fetchdf()

            rows = json_safe(
                result_dataframe.to_dict(
                    orient="records"
                )
            )

            return SQLExecutionResult(
                sql=sql,
                columns=[
                    str(column)
                    for column in result_dataframe.columns
                ],
                rows=rows,
            )

        except duckdb.Error as exc:
            raise SQLExecutionError(
                str(exc)
            ) from exc

        finally:
            try:
                connection.unregister("dataset")
            except duckdb.Error:
                pass

            connection.close()