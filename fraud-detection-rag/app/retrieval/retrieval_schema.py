from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.retrieval.retrieval_latency import RetrievalLatency


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """
    One chunk returned by the retriever.
    """

    chunk_id: str
    content: str
    score: float
    distance: float
    rank: int
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.chunk_id, str):
            raise TypeError("Retrieved chunk ID must be a string.")

        if not self.chunk_id.strip():
            raise ValueError("Retrieved chunk ID cannot be empty.")

        if not isinstance(self.content, str):
            raise TypeError("Retrieved chunk content must be a string.")

        if not self.content.strip():
            raise ValueError("Retrieved chunk content cannot be empty.")

        if not isinstance(self.rank, int):
            raise TypeError("Retrieved chunk rank must be an integer.")

        if self.rank < 1:
            raise ValueError("Retrieved chunk rank must be at least 1.")


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """
    Complete result of one retrieval operation.
    """

    query: str
    chunks: tuple[RetrievedChunk, ...]
    context: str
    total_context_characters: int
    candidates_considered: int
    filtered_count: int
    latency: RetrievalLatency

    def __post_init__(self) -> None:
        if not isinstance(self.query, str):
            raise TypeError("Retrieval query must be a string.")

        if not self.query.strip():
            raise ValueError("Retrieval query cannot be empty.")

        if not isinstance(self.context, str):
            raise TypeError("Retrieval context must be a string.")

        if self.total_context_characters < 0:
            raise ValueError("total_context_characters cannot be negative.")

        if self.candidates_considered < 0:
            raise ValueError("candidates_considered cannot be negative.")

        if self.filtered_count < 0:
            raise ValueError("filtered_count cannot be negative.")

        if self.filtered_count > self.candidates_considered:
            raise ValueError(
                "filtered_count cannot be greater than candidates_considered."
            )

        if self.total_context_characters != len(self.context):
            raise ValueError(
                "total_context_characters does not match the actual context length."
            )

        if not isinstance(self.latency, RetrievalLatency):
            raise TypeError("latency must be a RetrievalLatency instance.")

    def __len__(self) -> int:
        """
        Return the number of selected chunks.
        """

        return len(self.chunks)

    @property
    def is_empty(self) -> bool:
        """
        Return True when no chunks were retrieved.
        """

        return len(self.chunks) == 0
