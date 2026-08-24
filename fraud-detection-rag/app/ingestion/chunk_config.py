from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


DEFAULT_SEPARATORS: tuple[str, ...] = (
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
)


class ChunkConfig(BaseModel):
    """
    Configuration shared by chunking strategies.

    Size values currently represent characters rather than tokens.

    Character-based limits keep the chunking module independent of a specific
    tokenizer or embedding provider. Token-aware sizing can later be added
    through a dedicated length-calculation abstraction without changing the
    chunking interfaces.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    target_size: int = Field(
        default=1_000,
        ge=1,
        description="Preferred maximum size of a text segment in characters.",
    )

    overlap: int = Field(
        default=150,
        ge=0,
        description="Approximate content overlap between adjacent segments.",
    )

    min_chunk_size: int = Field(
        default=100,
        ge=1,
        description=(
            "Preferred minimum chunk size. Small final chunks may later be "
            "merged with neighbouring chunks when possible."
        ),
    )

    preserve_headings: bool = Field(
        default=True,
        description="Whether structural chunkers should preserve heading context.",
    )

    separators: tuple[str, ...] = Field(
        default=DEFAULT_SEPARATORS,
        min_length=1,
        description=(
            "Separators used from strongest to weakest semantic boundary. "
            "An empty string enables character-level fallback splitting."
        ),
    )

    strip_chunks: bool = Field(
        default=True,
        description="Strip surrounding whitespace from generated text segments.",
    )

    drop_empty_chunks: bool = Field(
        default=True,
        description="Remove empty or whitespace-only segments.",
    )

    @model_validator(mode="after")
    def validate_size_relationships(self) -> "ChunkConfig":
        """
        Validate relationships between chunk size settings.
        """

        if self.overlap >= self.target_size:
            raise ValueError(
                "Chunk overlap must be smaller than the target chunk size."
            )

        if self.min_chunk_size > self.target_size:
            raise ValueError(
                "Minimum chunk size cannot be greater than target chunk size."
            )

        if len(set(self.separators)) != len(self.separators):
            raise ValueError("Chunk separators must not contain duplicates.")

        if "" in self.separators and self.separators[-1] != "":
            raise ValueError(
                "The empty character-fallback separator must be the final separator."
            )

        return self
