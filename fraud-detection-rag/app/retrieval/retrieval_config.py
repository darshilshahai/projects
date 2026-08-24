from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RetrievalConfig(BaseModel):
    """
    Configuration for semantic retrieval.

    The retriever first requests fetch_k candidates from the vector store.
    It then removes weak and duplicate results before returning top_k chunks.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    top_k: int = Field(
        default=2,
        ge=1,
        le=100,
        description="Maximum final chunks returned.",
    )

    fetch_k: int = Field(
        default=5,
        ge=1,
        le=500,
        description=(
            "Number of candidates requested from the vector store before filtering."
        ),
    )

    minimum_score: float | None = Field(
        default=0.35,
        ge=-1.0,
        le=1.0,
        description=(
            "Minimum similarity score required for a result. "
            "Set to None to disable score filtering."
        ),
    )

    maximum_context_characters: int | None = Field(
        default=3_000,
        ge=1,
        description=("Maximum total number of retrieved document characters."),
    )

    remove_duplicate_content: bool = Field(
        default=True,
        description="Remove exactly duplicated content.",
    )

    remove_near_duplicate_content: bool = Field(
        default=True,
        description=(
            "Remove chunks containing mostly the same words, "
            "even when their word order is slightly different."
        ),
    )

    near_duplicate_similarity_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description=(
            "Jaccard similarity threshold used to identify near-duplicate chunks."
        ),
    )

    include_metadata: bool = Field(
        default=True,
        description="Include vector-store metadata in retrieved chunks.",
    )

    @model_validator(mode="after")
    def validate_limits(self) -> "RetrievalConfig":
        """
        Validate relationships between retrieval limits.
        """

        if self.fetch_k < self.top_k:
            raise ValueError("fetch_k must be greater than or equal to top_k.")

        return self
