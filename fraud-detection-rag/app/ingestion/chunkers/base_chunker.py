from __future__ import annotations

from abc import ABC, abstractmethod

from app.ingestion.chunk_config import ChunkConfig


class BaseChunker(ABC):
    """
    Abstract contract for text chunking strategies.

    A chunker has one responsibility:

        Given normalized text, return a sequence of text segments.

    It must not know about:

    - Document models
    - Chunk models
    - chunk IDs
    - source metadata
    - embeddings
    - vector databases
    - retrieval

    Those responsibilities belong to other pipeline components.
    """

    def __init__(self, config: ChunkConfig) -> None:
        """
        Initialize the chunking strategy.

        Args:
            config:
                Immutable configuration controlling the chunking behaviour.
        """

        self._config = config

    @property
    def config(self) -> ChunkConfig:
        """
        Return the immutable chunking configuration.
        """

        return self._config

    @abstractmethod
    def split(self, text: str) -> list[str]:
        """
        Split normalized text into retrieval-oriented segments.

        Implementations should preserve semantic boundaries whenever possible
        and must not return empty or whitespace-only segments.

        Args:
            text:
                Normalized source text.

        Returns:
            Ordered text segments.

        Raises:
            TypeError:
                When text is not a string.
        """

        raise NotImplementedError

    def _prepare_text(self, text: str) -> str:
        """
        Perform shared input validation before strategy-specific splitting.

        This method does not normalize text. Normalization is a separate
        pipeline responsibility handled by TextNormalizer.
        """

        return text.strip() if self.config.strip_chunks else text

    def _finalize_segments(self, segments: list[str]) -> list[str]:
        """
        Apply shared cleanup rules to strategy-generated segments.

        This gives all chunking strategies consistent behaviour without
        requiring each implementation to duplicate filtering logic.
        """

        finalized: list[str] = []

        for segment in segments:
            prepared = segment.strip() if self.config.strip_chunks else segment

            if self.config.drop_empty_chunks and not prepared.strip():
                continue

            finalized.append(prepared)

        return finalized
