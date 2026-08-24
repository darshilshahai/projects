from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ColumnProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    pandas_dtype: str
    duckdb_type: str
    nullable: bool
    null_count: int = Field(ge=0)
    unique_count: int = Field(ge=0)
    sample_values: list[Any]


class DatasetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: list[ColumnProfile]
    preview: list[dict[str, Any]]


class DatasetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    original_filename: str
    stored_filename: str
    content_type: str | None
    size_bytes: int = Field(ge=0)
    created_at: datetime
    profile: DatasetProfile


class DatasetUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    dataset: DatasetMetadata


class DatasetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    datasets: list[DatasetMetadata]
    count: int = Field(ge=0)


class DatasetPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    rows: list[dict[str, Any]]
    returned_rows: int = Field(ge=0)