from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """
    Represents a document after its text has been extracted.

    A Document is the input consumed by the ingestion pipeline. It contains
    the extracted textual content and metadata required to trace generated
    chunks back to their original source.

    The model intentionally does not contain chunk-specific information.
    Chunk identifiers, indexes, overlap information, and token counts belong
    to the Chunk model created later in the pipeline.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=False,
        validate_assignment=True,
    )

    content: str = Field(
        ...,
        description="Complete extracted text of the source document.",
    )

    source: str = Field(
        ...,
        min_length=1,
        description=(
            "Stable identifier for the source, such as a file path, URL, "
            "database record ID, or object-storage key."
        ),
    )

    file_type: str | None = Field(
        default=None,
        description="Normalized source type, such as pdf, txt, md, or html.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-level metadata propagated to generated chunks.",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """
        Reject documents that contain no meaningful text.

        Whitespace is preserved because the normalizer is responsible for
        transforming document content. Validation only checks whether the
        document contains at least one non-whitespace character.
        """

        if not value or not value.strip():
            raise ValueError("Document content cannot be empty or whitespace-only.")

        return value

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        """
        Remove accidental surrounding whitespace from the source identifier.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError("Document source cannot be empty.")

        return normalized

    @field_validator("file_type")
    @classmethod
    def normalize_file_type(cls, value: str | None) -> str | None:
        """
        Normalize file types to lowercase without a leading dot.

        Examples:
            ".PDF" -> "pdf"
            " TXT " -> "txt"
        """

        if value is None:
            return None

        normalized = value.strip().lower().removeprefix(".")

        return normalized or None
