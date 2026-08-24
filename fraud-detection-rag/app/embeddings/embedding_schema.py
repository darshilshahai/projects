from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EmbeddingBatch:
    """
    Represents the result of embedding multiple texts.

    Each input text has:

    - one input identifier
    - one original text
    - one embedding vector

    The position of each item must match across all three collections.
    """

    ids: tuple[str, ...]
    texts: tuple[str, ...]
    vectors: tuple[tuple[float, ...], ...]
    model_name: str
    dimension: int
    normalized: bool
    metadata: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        """
        Validate relationships between batch fields.
        """

        total_ids = len(self.ids)
        total_texts = len(self.texts)
        total_vectors = len(self.vectors)

        if total_ids != total_texts:
            raise ValueError(
                "EmbeddingBatch must contain the same number of IDs and texts."
            )

        if total_texts != total_vectors:
            raise ValueError(
                "EmbeddingBatch must contain the same number of texts and vectors."
            )

        if self.metadata and len(self.metadata) != total_texts:
            raise ValueError("EmbeddingBatch metadata must contain one entry per text.")

        if self.dimension <= 0:
            raise ValueError("Embedding dimension must be greater than zero.")

        if not self.model_name.strip():
            raise ValueError("Embedding model name cannot be empty.")

        for index, identifier in enumerate(self.ids):
            if not isinstance(identifier, str) or not identifier.strip():
                raise ValueError(
                    f"Embedding identifier at index {index} cannot be empty."
                )

        for index, text in enumerate(self.texts):
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Embedding text at index {index} cannot be empty.")

        for index, vector in enumerate(self.vectors):
            if len(vector) != self.dimension:
                raise ValueError(
                    f"Vector at index {index} has dimension {len(vector)}, "
                    f"but expected {self.dimension}."
                )

    def __len__(self) -> int:
        """
        Return the number of embedded texts.
        """

        return len(self.texts)

    @property
    def is_empty(self) -> bool:
        """
        Return True when the batch contains no embeddings.
        """

        return len(self.texts) == 0
