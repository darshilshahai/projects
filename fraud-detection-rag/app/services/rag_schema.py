from __future__ import annotations

from dataclasses import dataclass

from app.retrieval.retrieval_latency import RetrievalLatency
from app.retrieval.retrieval_schema import RetrievedChunk
from app.services.latency_schema import RAGLatency


@dataclass(frozen=True, slots=True)
class RAGSource:
    """
    Source information returned with a RAG answer.
    """

    number: int
    chunk_id: str
    source: str | None
    score: float
    content_preview: str

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Source number must be at least 1.")

        if not isinstance(self.chunk_id, str):
            raise TypeError("Source chunk ID must be a string.")

        if not self.chunk_id.strip():
            raise ValueError("Source chunk ID cannot be empty.")


@dataclass(frozen=True, slots=True)
class RAGResponse:
    """
    Final answer returned by the RAG service.
    """

    question: str
    answer: str
    sources: tuple[RAGSource, ...]
    retrieved_chunks: tuple[RetrievedChunk, ...]
    model_name: str | None
    provider: str | None
    latency: RAGLatency
    retrieval_latency: RetrievalLatency
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    answered_from_documents: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.question, str):
            raise TypeError("RAG question must be a string.")

        if not self.question.strip():
            raise ValueError("RAG question cannot be empty.")

        if not isinstance(self.answer, str):
            raise TypeError("RAG answer must be a string.")

        if not self.answer.strip():
            raise ValueError("RAG answer cannot be empty.")

        if not isinstance(self.latency, RAGLatency):
            raise TypeError("latency must be a RAGLatency instance.")

        if not isinstance(
            self.retrieval_latency,
            RetrievalLatency,
        ):
            raise TypeError("retrieval_latency must be a RetrievalLatency instance.")
