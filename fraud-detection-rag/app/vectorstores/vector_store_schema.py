from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchResult:
    """
    One result returned by a vector similarity search.
    """

    id: str
    document: str
    metadata: dict[str, Any]
    distance: float
    score: float
    rank: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Search result ID cannot be empty.")

        if not self.document.strip():
            raise ValueError("Search result document cannot be empty.")

        if self.rank < 1:
            raise ValueError("Search result rank must be at least 1.")


@dataclass(frozen=True, slots=True)
class SearchResults:
    """
    Complete result returned for one search query.
    """

    query: str | None
    results: tuple[SearchResult, ...]
    collection_name: str

    def __post_init__(self) -> None:
        if not self.collection_name.strip():
            raise ValueError("Collection name cannot be empty.")

    def __len__(self) -> int:
        return len(self.results)

    @property
    def is_empty(self) -> bool:
        return len(self.results) == 0
