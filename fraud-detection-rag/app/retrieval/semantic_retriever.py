from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Mapping
from typing import Any

from app.embeddings.base_embedder import BaseEmbedder
from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.retrieval_config import RetrievalConfig
from app.retrieval.retrieval_latency import RetrievalLatency
from app.retrieval.retrieval_schema import (
    RetrievedChunk,
    RetrievalResult,
)
from app.vectorstores.base_vector_store import BaseVectorStore
from app.vectorstores.vector_store_schema import SearchResult


class SemanticRetriever(BaseRetriever):
    """
    Retrieve relevant chunks using vector similarity search.

    Processing flow:

        Query
          ↓
        Query embedding
          ↓
        Vector search
          ↓
        Score filtering
          ↓
        Exact duplicate removal
          ↓
        Near-duplicate removal
          ↓
        Context-size limiting
          ↓
        RetrievalResult
    """

    _WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+")

    def __init__(
        self,
        *,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        config: RetrievalConfig | None = None,
    ) -> None:
        if not isinstance(embedder, BaseEmbedder):
            raise TypeError(
                "embedder must be an instance of BaseEmbedder, "
                f"received {type(embedder).__name__}."
            )

        if not isinstance(vector_store, BaseVectorStore):
            raise TypeError(
                "vector_store must be an instance of BaseVectorStore, "
                f"received {type(vector_store).__name__}."
            )

        if config is not None and not isinstance(config, RetrievalConfig):
            raise TypeError(
                "config must be a RetrievalConfig or None, "
                f"received {type(config).__name__}."
            )

        self._embedder = embedder
        self._vector_store = vector_store
        self._config = config or RetrievalConfig()

    @property
    def embedder(self) -> BaseEmbedder:
        return self._embedder

    @property
    def vector_store(self) -> BaseVectorStore:
        return self._vector_store

    @property
    def config(self) -> RetrievalConfig:
        return self._config

    def retrieve(
        self,
        query: str,
        *,
        where: Mapping[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks and record latency for each stage.
        """

        total_started_at = time.perf_counter()

        prepared_query = self._prepare_query(query)
        final_top_k = self._resolve_top_k(top_k)
        prepared_where = self._prepare_where(where)

        # -----------------------------------------------------
        # Query embedding
        # -----------------------------------------------------

        embedding_started_at = time.perf_counter()

        query_vector = self.embedder.embed_query(prepared_query)

        query_embedding_ms = self._elapsed_ms(embedding_started_at)

        # -----------------------------------------------------
        # Vector search
        # -----------------------------------------------------

        search_started_at = time.perf_counter()

        search_results = self.vector_store.search(
            query_vector,
            top_k=self.config.fetch_k,
            query=prepared_query,
            where=prepared_where,
        )

        vector_search_ms = self._elapsed_ms(search_started_at)

        # -----------------------------------------------------
        # Result filtering and context creation
        # -----------------------------------------------------

        processing_started_at = time.perf_counter()

        candidates = list(search_results.results)
        candidates_considered = len(candidates)

        selected_results = self._select_results(
            candidates=candidates,
            top_k=final_top_k,
        )

        retrieved_chunks = self._build_retrieved_chunks(selected_results)

        context = self._build_context(retrieved_chunks)

        result_processing_ms = self._elapsed_ms(processing_started_at)

        total_ms = self._elapsed_ms(total_started_at)

        return RetrievalResult(
            query=prepared_query,
            chunks=tuple(retrieved_chunks),
            context=context,
            total_context_characters=len(context),
            candidates_considered=candidates_considered,
            filtered_count=(candidates_considered - len(retrieved_chunks)),
            latency=RetrievalLatency(
                query_embedding_ms=query_embedding_ms,
                vector_search_ms=vector_search_ms,
                result_processing_ms=result_processing_ms,
                total_ms=total_ms,
            ),
        )

    @staticmethod
    def _prepare_query(query: str) -> str:
        """
        Validate and normalize a user query.
        """

        if not isinstance(query, str):
            raise TypeError(
                f"Retrieval query must be a string, received {type(query).__name__}."
            )

        prepared = query.strip()

        if not prepared:
            raise ValueError("Retrieval query cannot be empty.")

        return prepared

    def _resolve_top_k(
        self,
        top_k: int | None,
    ) -> int:
        """
        Resolve the number of final results.
        """

        if top_k is None:
            return self.config.top_k

        if not isinstance(top_k, int):
            raise TypeError("top_k must be an integer or None.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        if top_k > self.config.fetch_k:
            raise ValueError(
                "Per-request top_k cannot be greater than the configured fetch_k."
            )

        return top_k

    @staticmethod
    def _prepare_where(
        where: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        """
        Validate and copy metadata filters.
        """

        if where is None:
            return None

        if not isinstance(where, Mapping):
            raise TypeError(
                f"where must be a mapping, received {type(where).__name__}."
            )

        return dict(where)

    def _select_results(
        self,
        *,
        candidates: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        """
        Select useful results while removing weak and repeated chunks.
        """

        selected: list[SearchResult] = []

        seen_content_hashes: set[str] = set()
        selected_token_sets: list[set[str]] = []

        current_context_size = 0

        for candidate in candidates:
            if not candidate.document.strip():
                continue

            if not self._passes_score_threshold(candidate):
                continue

            content_hash = self._content_hash(candidate.document)

            if (
                self.config.remove_duplicate_content
                and content_hash in seen_content_hashes
            ):
                continue

            candidate_tokens = self._content_tokens(candidate.document)

            if self.config.remove_near_duplicate_content and self._is_near_duplicate(
                candidate_tokens=candidate_tokens,
                selected_token_sets=selected_token_sets,
            ):
                continue

            projected_size = self._projected_context_size(
                current_size=current_context_size,
                new_content=candidate.document,
                has_existing_results=bool(selected),
            )

            maximum_size = self.config.maximum_context_characters

            if maximum_size is not None and projected_size > maximum_size:
                continue

            selected.append(candidate)
            current_context_size = projected_size

            seen_content_hashes.add(content_hash)
            selected_token_sets.append(candidate_tokens)

            if len(selected) >= top_k:
                break

        return selected

    def _passes_score_threshold(
        self,
        result: SearchResult,
    ) -> bool:
        """
        Return True when a result meets the score threshold.
        """

        minimum_score = self.config.minimum_score

        if minimum_score is None:
            return True

        return result.score >= minimum_score

    @staticmethod
    def _content_hash(content: str) -> str:
        """
        Create an exact duplicate-detection hash.
        """

        normalized = " ".join(content.lower().split())

        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @classmethod
    def _content_tokens(
        cls,
        content: str,
    ) -> set[str]:
        """
        Convert content into normalized words.

        A set is used because near-duplicate detection compares the words
        present in each chunk, not their exact ordering.
        """

        return {match.group(0).lower() for match in cls._WORD_PATTERN.finditer(content)}

    def _is_near_duplicate(
        self,
        *,
        candidate_tokens: set[str],
        selected_token_sets: list[set[str]],
    ) -> bool:
        """
        Check whether candidate content is too similar to selected content.

        Jaccard similarity:

            shared words / all unique words
        """

        if not candidate_tokens:
            return False

        threshold = self.config.near_duplicate_similarity_threshold

        for selected_tokens in selected_token_sets:
            if not selected_tokens:
                continue

            intersection_size = len(candidate_tokens.intersection(selected_tokens))

            union_size = len(candidate_tokens.union(selected_tokens))

            if union_size == 0:
                continue

            similarity = intersection_size / union_size

            if similarity >= threshold:
                return True

        return False

    @staticmethod
    def _projected_context_size(
        *,
        current_size: int,
        new_content: str,
        has_existing_results: bool,
    ) -> int:
        """
        Calculate context size after adding one result.
        """

        separator_size = 2 if has_existing_results else 0

        return current_size + separator_size + len(new_content)

    def _build_retrieved_chunks(
        self,
        results: list[SearchResult],
    ) -> list[RetrievedChunk]:
        """
        Convert vector-store records into retrieval models.
        """

        chunks: list[RetrievedChunk] = []

        for index, result in enumerate(results):
            metadata = dict(result.metadata) if self.config.include_metadata else {}

            source_value = result.metadata.get("source")

            source = str(source_value) if source_value is not None else None

            chunks.append(
                RetrievedChunk(
                    chunk_id=result.id,
                    content=result.document,
                    score=result.score,
                    distance=result.distance,
                    rank=index + 1,
                    source=source,
                    metadata=metadata,
                )
            )

        return chunks

    @staticmethod
    def _build_context(
        chunks: list[RetrievedChunk],
    ) -> str:
        """
        Combine selected chunks into final retrieval context.
        """

        context_sections: list[str] = []

        for chunk in chunks:
            source = chunk.source or "Unknown source"

            context_sections.append(
                (f"[Source {chunk.rank}]\nSource: {source}\nContent:\n{chunk.content}")
            )

        return "\n\n".join(context_sections)

    @staticmethod
    def _elapsed_ms(
        started_at: float,
    ) -> float:
        """
        Calculate elapsed milliseconds.
        """

        return round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )
