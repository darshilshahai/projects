from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.embeddings.embedding_config import EmbeddingConfig
from app.embeddings.embedding_schema import EmbeddingBatch
from app.ingestion.chunk_schema import Chunk


class BaseEmbedder(ABC):
    """
    Common interface for all embedding providers.

    Future implementations may include:

    - Sentence Transformers
    - OpenAI embeddings
    - Google embeddings
    - Cohere embeddings
    - Voyage AI embeddings
    - local Hugging Face models

    Application code should depend on BaseEmbedder rather than one specific
    provider.
    """

    def __init__(self, config: EmbeddingConfig) -> None:
        self._config = config

    @property
    def config(self) -> EmbeddingConfig:
        """
        Return the immutable embedding configuration.
        """

        return self._config

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the size of one embedding vector.
        """

        raise NotImplementedError

    @abstractmethod
    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        ids: Sequence[str] | None = None,
        metadata: Sequence[Mapping[str, Any]] | None = None,
    ) -> EmbeddingBatch:
        """
        Convert multiple texts into embedding vectors.
        """

        raise NotImplementedError

    def embed_query(self, query: str) -> tuple[float, ...]:
        """
        Embed one user query.

        Query embedding uses the same model and vector space as document
        embeddings.
        """

        prepared_query = query.strip()

        if not prepared_query:
            raise ValueError("Embedding query cannot be empty.")

        result = self.embed_texts(
            [prepared_query],
            ids=["query"],
        )

        return result.vectors[0]

    def embed_chunks(
        self,
        chunks: Sequence[Chunk],
    ) -> EmbeddingBatch:
        """
        Embed validated Chunk objects.

        Chunk IDs, content, and metadata are preserved in the result.
        """

        if isinstance(chunks, (str, bytes)):
            raise TypeError("embed_chunks expected a sequence of Chunk objects.")

        ids: list[str] = []
        texts: list[str] = []
        metadata: list[Mapping[str, Any]] = []

        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, Chunk):
                raise TypeError(
                    "embed_chunks expected every item to be a Chunk, "
                    f"but item {index} is {type(chunk).__name__}."
                )

            ids.append(chunk.chunk_id)
            texts.append(chunk.content)
            metadata.append(
                {
                    **chunk.metadata,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                }
            )

        return self.embed_texts(
            texts,
            ids=ids,
            metadata=metadata,
        )
