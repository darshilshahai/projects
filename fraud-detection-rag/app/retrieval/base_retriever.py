from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from app.retrieval.retrieval_schema import RetrievalResult


class BaseRetriever(ABC):
    """
    Common interface for retrieval implementations.

    Future implementations may include:

    - semantic vector retrieval
    - keyword retrieval
    - hybrid retrieval
    - reranked retrieval
    - multi-query retrieval
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        where: Mapping[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant document chunks for one user query.
        """

        raise NotImplementedError
