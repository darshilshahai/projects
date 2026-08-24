from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmbeddingConfig(BaseModel):
    """
    Configuration used by embedding implementations.

    The configuration is immutable so embedding behaviour cannot change
    accidentally while the application is running.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        min_length=1,
        description="Name or local path of the embedding model.",
    )

    batch_size: int = Field(
        default=32,
        ge=1,
        le=1024,
        description="Number of texts processed in one model call.",
    )

    normalize_embeddings: bool = Field(
        default=True,
        description=(
            "Whether vectors should be normalized to unit length. "
            "This is useful when cosine similarity is used."
        ),
    )

    device: str | None = Field(
        default=None,
        description=(
            "Execution device, such as cpu, cuda, or mps. "
            "When omitted, the model library chooses automatically."
        ),
    )

    show_progress_bar: bool = Field(
        default=False,
        description="Whether model encoding should display a progress bar.",
    )

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, value: str) -> str:
        """
        Remove accidental whitespace around the model name.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError("Embedding model name cannot be empty.")

        return normalized

    @field_validator("device")
    @classmethod
    def normalize_device(cls, value: str | None) -> str | None:
        """
        Normalize optional device names.

        Examples:

            " CPU " -> "cpu"
            "MPS"   -> "mps"
        """

        if value is None:
            return None

        normalized = value.strip().lower()

        return normalized or None
