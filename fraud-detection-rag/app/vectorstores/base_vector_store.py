from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.embeddings.embedding_schema import EmbeddingBatch
from app.vectorstores.vector_store_schema import SearchResults


class BaseVectorStore(ABC):
    """
    Common interface for vector database implementations.

    Future implementations may include:

    - ChromaDB
    - Qdrant
    - Pinecone
    - Weaviate
    - PostgreSQL with pgvector
    """

    @abstractmethod
    def upsert(self, batch: EmbeddingBatch) -> int:
        """
        Insert new records or update existing records.

        Returns:
            Number of records processed.
        """

        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: Sequence[float],
        *,
        top_k: int = 5,
        query: str | None = None,
        where: Mapping[str, Any] | None = None,
    ) -> SearchResults:
        """
        Search for records similar to the query vector.
        """

        raise NotImplementedError

    @abstractmethod
    def delete(self, ids: Sequence[str]) -> int:
        """
        Delete records using their IDs.

        Returns:
            Number of requested IDs.
        """

        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """
        Return the number of records in the collection.
        """

        raise NotImplementedError
