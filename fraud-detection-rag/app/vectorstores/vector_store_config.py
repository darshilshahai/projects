from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


DistanceMetric = Literal["cosine", "l2", "ip"]


class VectorStoreConfig(BaseModel):
    """
    Configuration for the vector store.

    This configuration tells Chroma:

    - where to store data
    - which collection to use
    - which distance metric to use
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    persist_directory: Path = Field(
        default=Path("data/chroma"),
        description="Directory where Chroma stores its local database.",
    )

    collection_name: str = Field(
        default="rag_documents",
        min_length=3,
        description="Name of the Chroma collection.",
    )

    distance_metric: DistanceMetric = Field(
        default="cosine",
        description="Distance metric used to compare vectors.",
    )

    expected_dimension: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Expected embedding vector dimension. "
            "When provided, vectors are validated before storage and search."
        ),
    )

    @field_validator("collection_name")
    @classmethod
    def normalize_collection_name(cls, value: str) -> str:
        """
        Clean and validate the collection name.
        """

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("Collection name cannot be empty.")

        return normalized

    @field_validator("persist_directory")
    @classmethod
    def normalize_directory(cls, value: Path) -> Path:
        """
        Expand values such as ~/data/chroma.
        """

        return value.expanduser()
