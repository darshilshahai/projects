from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from app.core.exceptions import InvalidCSVError
from app.schemas.dataset import ColumnProfile, DatasetProfile
from app.utils.files import json_safe


class DatasetProfiler:
    def __init__(
        self,
        *,
        sample_rows: int,
        preview_rows: int,
    ) -> None:
        self._sample_rows = sample_rows
        self._preview_rows = preview_rows

    def load_csv(self, csv_path: Path) -> pd.DataFrame:
        try:
            dataframe = pd.read_csv(
                csv_path,
                low_memory=False,
                encoding="utf-8",
            )
        except UnicodeDecodeError:
            try:
                dataframe = pd.read_csv(
                    csv_path,
                    low_memory=False,
                    encoding="latin-1",
                )
            except Exception as exc:
                raise InvalidCSVError(str(exc)) from exc
        except pd.errors.EmptyDataError as exc:
            raise InvalidCSVError("the file contains no columns") from exc
        except pd.errors.ParserError as exc:
            raise InvalidCSVError(str(exc)) from exc
        except Exception as exc:
            raise InvalidCSVError(str(exc)) from exc

        if dataframe.columns.empty:
            raise InvalidCSVError("the file contains no columns")

        dataframe.columns = self._normalize_columns(dataframe.columns.tolist())

        return dataframe

    def create_profile(self, dataframe: pd.DataFrame) -> DatasetProfile:
        duckdb_types = self._get_duckdb_types(dataframe)
        columns: list[ColumnProfile] = []

        for column_name in dataframe.columns:
            series = dataframe[column_name]
            non_null_values = series.dropna()

            sample_values = (
                non_null_values.drop_duplicates()
                .head(self._sample_rows)
                .tolist()
            )

            columns.append(
                ColumnProfile(
                    name=column_name,
                    pandas_dtype=str(series.dtype),
                    duckdb_type=duckdb_types.get(column_name, "UNKNOWN"),
                    nullable=bool(series.isna().any()),
                    null_count=int(series.isna().sum()),
                    unique_count=int(series.nunique(dropna=True)),
                    sample_values=json_safe(sample_values),
                )
            )

        preview = json_safe(
            dataframe.head(self._preview_rows).to_dict(orient="records")
        )

        return DatasetProfile(
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            columns=columns,
            preview=preview,
        )

    def preview(
        self,
        dataframe: pd.DataFrame,
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        return json_safe(dataframe.head(limit).to_dict(orient="records"))

    def _get_duckdb_types(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, str]:
        connection = duckdb.connect(database=":memory:")

        try:
            connection.register("dataset", dataframe)
            description = connection.execute(
                "DESCRIBE SELECT * FROM dataset"
            ).fetchall()

            return {
                str(row[0]): str(row[1])
                for row in description
            }
        finally:
            try:
                connection.unregister("dataset")
            except duckdb.Error:
                pass

            connection.close()

    @staticmethod
    def _normalize_columns(columns: list[Any]) -> list[str]:
        normalized_columns: list[str] = []
        seen: dict[str, int] = {}

        for index, original_column in enumerate(columns, start=1):
            base_name = str(original_column).strip()

            if not base_name:
                base_name = f"column_{index}"

            duplicate_index = seen.get(base_name, 0)
            seen[base_name] = duplicate_index + 1

            if duplicate_index == 0:
                normalized_columns.append(base_name)
            else:
                normalized_columns.append(
                    f"{base_name}_{duplicate_index + 1}"
                )

        return normalized_columns