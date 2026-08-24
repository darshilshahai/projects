from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.api.dependencies import get_rag_service
from app.services.rag_service import RAGService
from app.services.streaming_schema import (
    RAGStreamEvent,
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


class RAGQuestionRequest(BaseModel):
    """
    Request used by both normal and streaming RAG endpoints.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    question: str = Field(
        ...,
        min_length=1,
        description=(
            "Question to answer from stored documents."
        ),
    )

    tenant_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Tenant whose documents may be searched."
        ),
    )

    category: str | None = Field(
        default=None,
        description=(
            "Optional document-category filter."
        ),
    )

    top_k: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description=(
            "Optional number of chunks to retrieve."
        ),
    )

    additional_filters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional Chroma metadata filters."
        ),
    )

    @field_validator(
        "question",
        "tenant_id",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        prepared = value.strip()

        if not prepared:
            raise ValueError(
                "Required request value cannot be empty."
            )

        return prepared

    @field_validator("category")
    @classmethod
    def normalize_category(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        prepared = value.strip().lower()

        return prepared or None


class RAGSourceResponse(BaseModel):
    """
    One retrieved source.
    """

    number: int
    chunk_id: str
    source: str | None
    score: float
    content_preview: str


class RetrievalLatencyResponse(BaseModel):
    """
    Detailed retrieval timing in milliseconds.
    """

    query_embedding_ms: float
    vector_search_ms: float
    result_processing_ms: float
    total_ms: float


class RAGLatencyResponse(BaseModel):
    """
    Complete non-streaming RAG timing.
    """

    retrieval_ms: float
    prompt_building_ms: float
    llm_generation_ms: float
    source_building_ms: float
    total_ms: float


class RAGAnswerResponse(BaseModel):
    """
    Complete non-streaming answer response.
    """

    success: bool = True
    question: str
    answer: str
    answered_from_documents: bool
    sources: list[RAGSourceResponse]
    model_name: str | None
    provider: str | None
    response_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency: RAGLatencyResponse
    retrieval_latency: RetrievalLatencyResponse


@router.post(
    "/ask",
    response_model=RAGAnswerResponse,
    summary="Ask a question and receive complete JSON",
)
def ask_question(
    request: RAGQuestionRequest,
    rag_service: RAGService = Depends(
        get_rag_service
    ),
) -> RAGAnswerResponse:
    """
    Return the complete RAG answer after generation finishes.
    """

    where_filter = _build_where_filter(
        request
    )

    response = rag_service.ask(
        request.question,
        where=where_filter,
        top_k=request.top_k,
    )

    return RAGAnswerResponse(
        question=response.question,
        answer=response.answer,
        answered_from_documents=(
            response.answered_from_documents
        ),
        sources=[
            RAGSourceResponse(
                number=source.number,
                chunk_id=source.chunk_id,
                source=source.source,
                score=source.score,
                content_preview=(
                    source.content_preview
                ),
            )
            for source in response.sources
        ],
        model_name=response.model_name,
        provider=response.provider,
        response_id=response.response_id,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        total_tokens=response.total_tokens,
        latency=RAGLatencyResponse(
            retrieval_ms=(
                response.latency.retrieval_ms
            ),
            prompt_building_ms=(
                response.latency.prompt_building_ms
            ),
            llm_generation_ms=(
                response.latency.llm_generation_ms
            ),
            source_building_ms=(
                response.latency.source_building_ms
            ),
            total_ms=response.latency.total_ms,
        ),
        retrieval_latency=RetrievalLatencyResponse(
            query_embedding_ms=(
                response
                .retrieval_latency
                .query_embedding_ms
            ),
            vector_search_ms=(
                response
                .retrieval_latency
                .vector_search_ms
            ),
            result_processing_ms=(
                response
                .retrieval_latency
                .result_processing_ms
            ),
            total_ms=(
                response
                .retrieval_latency
                .total_ms
            ),
        ),
    )


@router.post(
    "/ask/stream",
    summary="Ask a question and stream the answer",
    response_class=StreamingResponse,
)
def stream_question(
    request: RAGQuestionRequest,
    rag_service: RAGService = Depends(
        get_rag_service
    ),
) -> StreamingResponse:
    """
    Stream a RAG answer using Server-Sent Events.

    Response content type:

        text/event-stream
    """

    where_filter = _build_where_filter(
        request
    )

    event_iterator = rag_service.stream(
        request.question,
        where=where_filter,
        top_k=request.top_k,
    )

    return StreamingResponse(
        _encode_sse_events(event_iterator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _encode_sse_events(
    events: Iterator[RAGStreamEvent],
) -> Iterator[str]:
    """
    Convert domain stream events into SSE-formatted strings.

    SSE event format:

        event: token
        data: {"delta":"hello"}

    Each event ends with two newline characters.
    """

    for stream_event in events:
        serialized_data = json.dumps(
            stream_event.data,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        yield (
            f"event: {stream_event.event}\n"
            f"data: {serialized_data}\n\n"
        )


def _build_where_filter(
    request: RAGQuestionRequest,
) -> dict[str, Any]:
    """
    Build metadata filters.

    Tenant filtering is always applied.
    """

    filters: list[dict[str, Any]] = [
        {
            "tenant_id": request.tenant_id,
        }
    ]

    if request.category is not None:
        filters.append(
            {
                "category": request.category,
            }
        )

    for key, value in request.additional_filters.items():
        if key in {
            "tenant_id",
            "category",
        }:
            continue

        filters.append(
            {
                key: value,
            }
        )

    if len(filters) == 1:
        return filters[0]

    return {
        "$and": filters,
    }