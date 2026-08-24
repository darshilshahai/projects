from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Chunk(BaseModel):
    """
    Represents a retrieval-ready segment created from a source document.

    Chunks are produced after normalization, splitting, overlap processing,
    metadata enrichment, and ID generation.

    The Chunk model is independent of any particular vector database.
    ChromaDB, Qdrant, Pinecone, Weaviate, PostgreSQL/pgvector, and other
    storage adapters can translate this model into their native formats.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    chunk_id: str = Field(
        ...,
        min_length=1,
        description="Stable and unique identifier for the chunk.",
    )

    chunk_index: int = Field(
        ...,
        ge=0,
        description="Zero-based position of the chunk within its source document.",
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Text that will be embedded and retrieved.",
    )

    source: str = Field(
        ...,
        min_length=1,
        description="Identifier of the source document.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document and chunk-level metadata used during retrieval.",
    )

    @field_validator("chunk_id", "source")
    @classmethod
    def validate_non_empty_identifier(cls, value: str) -> str:
        """
        Normalize and validate identifiers.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError("Identifier cannot be empty.")

        return normalized

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """
        Reject empty or whitespace-only chunks.
        """

        if not value or not value.strip():
            raise ValueError("Chunk content cannot be empty or whitespace-only.")

        return value
