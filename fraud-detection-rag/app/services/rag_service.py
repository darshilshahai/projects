from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from dataclasses import asdict
from typing import Any

from app.llm.base_llm import BaseLLM
from app.prompts.rag_prompt_builder import (
    RAGPromptBuilder,
)
from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.retrieval_schema import (
    RetrievalResult,
)
from app.services.latency_schema import RAGLatency
from app.services.rag_schema import (
    RAGResponse,
    RAGSource,
)
from app.services.streaming_schema import (
    RAGStreamEvent,
    StreamingLatency,
)


class RAGServiceError(RuntimeError):
    """
    Base error raised by the RAG service.
    """


class RetrievalFailedError(RAGServiceError):
    """
    Raised when document retrieval fails.
    """


class AnswerGenerationFailedError(RAGServiceError):
    """
    Raised when prompt construction or generation fails.
    """


class RAGService:
    """
    Coordinate retrieval and answer generation.

    Supports:

    - complete non-streaming responses
    - incremental streaming responses
    """

    DEFAULT_EMPTY_RETRIEVAL_ANSWER = (
        "I could not find enough relevant information "
        "in the available documents to answer this question."
    )

    def __init__(
        self,
        *,
        retriever: BaseRetriever,
        llm: BaseLLM,
        prompt_builder: RAGPromptBuilder | None = None,
        empty_retrieval_answer: str | None = None,
    ) -> None:
        if not isinstance(retriever, BaseRetriever):
            raise TypeError(
                "retriever must be an instance of BaseRetriever, "
                f"received {type(retriever).__name__}."
            )

        if not isinstance(llm, BaseLLM):
            raise TypeError(
                f"llm must be an instance of BaseLLM, received {type(llm).__name__}."
            )

        if prompt_builder is not None and not isinstance(
            prompt_builder,
            RAGPromptBuilder,
        ):
            raise TypeError("prompt_builder must be a RAGPromptBuilder or None.")

        selected_empty_answer = (
            empty_retrieval_answer
            if empty_retrieval_answer is not None
            else self.DEFAULT_EMPTY_RETRIEVAL_ANSWER
        )

        if not isinstance(selected_empty_answer, str):
            raise TypeError("empty_retrieval_answer must be a string.")

        normalized_empty_answer = selected_empty_answer.strip()

        if not normalized_empty_answer:
            raise ValueError("empty_retrieval_answer cannot be empty.")

        self._retriever = retriever
        self._llm = llm
        self._prompt_builder = prompt_builder or RAGPromptBuilder()
        self._empty_retrieval_answer = normalized_empty_answer

    @property
    def retriever(self) -> BaseRetriever:
        return self._retriever

    @property
    def llm(self) -> BaseLLM:
        return self._llm

    @property
    def prompt_builder(self) -> RAGPromptBuilder:
        return self._prompt_builder

    def ask(
        self,
        question: str,
        *,
        where: Mapping[str, Any] | None = None,
        top_k: int | None = None,
    ) -> RAGResponse:
        """
        Generate and return one complete RAG answer.
        """

        total_started_at = time.perf_counter()

        prepared_question = self._prepare_question(question)

        retrieval_started_at = time.perf_counter()

        retrieval_result = self._retrieve(
            question=prepared_question,
            where=where,
            top_k=top_k,
        )

        retrieval_ms = self._elapsed_ms(retrieval_started_at)

        if retrieval_result.is_empty:
            total_ms = self._elapsed_ms(total_started_at)

            return RAGResponse(
                question=prepared_question,
                answer=self._empty_retrieval_answer,
                sources=(),
                retrieved_chunks=(),
                model_name=None,
                provider=None,
                answered_from_documents=False,
                latency=RAGLatency(
                    retrieval_ms=retrieval_ms,
                    prompt_building_ms=0.0,
                    llm_generation_ms=0.0,
                    source_building_ms=0.0,
                    total_ms=total_ms,
                ),
                retrieval_latency=(retrieval_result.latency),
            )

        try:
            prompt_started_at = time.perf_counter()

            llm_request = self.prompt_builder.build(
                question=prepared_question,
                retrieval_result=retrieval_result,
            )

            prompt_building_ms = self._elapsed_ms(prompt_started_at)

            llm_started_at = time.perf_counter()

            llm_response = self.llm.generate(llm_request)

            llm_generation_ms = self._elapsed_ms(llm_started_at)

        except Exception as exc:
            raise AnswerGenerationFailedError(
                "Failed to generate an answer from retrieved context."
            ) from exc

        source_started_at = time.perf_counter()

        sources = self._build_sources(retrieval_result)

        source_building_ms = self._elapsed_ms(source_started_at)

        total_ms = self._elapsed_ms(total_started_at)

        return RAGResponse(
            question=prepared_question,
            answer=llm_response.text,
            sources=tuple(sources),
            retrieved_chunks=(retrieval_result.chunks),
            model_name=llm_response.model_name,
            provider=llm_response.provider,
            response_id=llm_response.response_id,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            total_tokens=llm_response.total_tokens,
            answered_from_documents=True,
            latency=RAGLatency(
                retrieval_ms=retrieval_ms,
                prompt_building_ms=prompt_building_ms,
                llm_generation_ms=llm_generation_ms,
                source_building_ms=source_building_ms,
                total_ms=total_ms,
            ),
            retrieval_latency=(retrieval_result.latency),
        )

    def stream(
        self,
        question: str,
        *,
        where: Mapping[str, Any] | None = None,
        top_k: int | None = None,
    ) -> Iterator[RAGStreamEvent]:
        """
        Stream one RAG answer.

        Event sequence:

            metadata
            token
            token
            ...
            complete

        When an error occurs after streaming starts, an error event is sent.
        """

        total_started_at = time.perf_counter()

        try:
            prepared_question = self._prepare_question(question)

            retrieval_started_at = time.perf_counter()

            retrieval_result = self._retrieve(
                question=prepared_question,
                where=where,
                top_k=top_k,
            )

            retrieval_ms = self._elapsed_ms(retrieval_started_at)

            source_started_at = time.perf_counter()

            sources = self._build_sources(retrieval_result)

            source_building_ms = self._elapsed_ms(source_started_at)

            yield RAGStreamEvent(
                event="metadata",
                data={
                    "question": prepared_question,
                    "answered_from_documents": (not retrieval_result.is_empty),
                    "sources": [asdict(source) for source in sources],
                    "retrieval_latency": asdict(retrieval_result.latency),
                },
            )

            if retrieval_result.is_empty:
                answer = self._empty_retrieval_answer

                yield RAGStreamEvent(
                    event="token",
                    data={
                        "delta": answer,
                    },
                )

                total_ms = self._elapsed_ms(total_started_at)

                yield RAGStreamEvent(
                    event="complete",
                    data={
                        "answer": answer,
                        "answered_from_documents": False,
                        "model_name": None,
                        "provider": None,
                        "response_id": None,
                        "usage": {
                            "input_tokens": None,
                            "output_tokens": None,
                            "total_tokens": None,
                        },
                        "latency": StreamingLatency(
                            retrieval_ms=retrieval_ms,
                            prompt_building_ms=0.0,
                            time_to_first_token_ms=(total_ms),
                            llm_generation_ms=0.0,
                            source_building_ms=(source_building_ms),
                            total_ms=total_ms,
                        ).to_dict(),
                    },
                )

                return

            prompt_started_at = time.perf_counter()

            llm_request = self.prompt_builder.build(
                question=prepared_question,
                retrieval_result=retrieval_result,
            )

            prompt_building_ms = self._elapsed_ms(prompt_started_at)

            llm_started_at = time.perf_counter()

            first_token_ms: float | None = None
            answer_parts: list[str] = []

            response_id: str | None = None
            model_name: str | None = None
            provider: str | None = None

            input_tokens: int | None = None
            output_tokens: int | None = None
            total_tokens: int | None = None

            for llm_event in self.llm.stream(llm_request):
                if llm_event.type == "text_delta":
                    if first_token_ms is None:
                        first_token_ms = self._elapsed_ms(total_started_at)

                    answer_parts.append(llm_event.delta)

                    yield RAGStreamEvent(
                        event="token",
                        data={
                            "delta": llm_event.delta,
                        },
                    )

                elif llm_event.type == "completed":
                    response_id = llm_event.response_id
                    model_name = llm_event.model_name
                    provider = llm_event.provider

                    input_tokens = llm_event.input_tokens
                    output_tokens = llm_event.output_tokens
                    total_tokens = llm_event.total_tokens

            llm_generation_ms = self._elapsed_ms(llm_started_at)

            complete_answer = "".join(answer_parts).strip()

            if not complete_answer:
                raise AnswerGenerationFailedError("The LLM stream returned no text.")

            total_ms = self._elapsed_ms(total_started_at)

            yield RAGStreamEvent(
                event="complete",
                data={
                    "answer": complete_answer,
                    "answered_from_documents": True,
                    "model_name": model_name,
                    "provider": provider,
                    "response_id": response_id,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                    },
                    "latency": StreamingLatency(
                        retrieval_ms=retrieval_ms,
                        prompt_building_ms=(prompt_building_ms),
                        time_to_first_token_ms=(first_token_ms),
                        llm_generation_ms=(llm_generation_ms),
                        source_building_ms=(source_building_ms),
                        total_ms=total_ms,
                    ).to_dict(),
                },
            )

        except Exception as exc:
            yield RAGStreamEvent(
                event="error",
                data={
                    "code": "STREAM_GENERATION_FAILED",
                    "message": ("The answer stream was interrupted."),
                    "details": str(exc),
                },
            )

    def _retrieve(
        self,
        *,
        question: str,
        where: Mapping[str, Any] | None,
        top_k: int | None,
    ) -> RetrievalResult:
        """
        Retrieve document context.
        """

        try:
            return self.retriever.retrieve(
                question,
                where=where,
                top_k=top_k,
            )
        except Exception as exc:
            raise RetrievalFailedError(
                "Failed to retrieve relevant document context."
            ) from exc

    @staticmethod
    def _prepare_question(
        question: str,
    ) -> str:
        """
        Validate the question.
        """

        if not isinstance(question, str):
            raise TypeError(
                f"Question must be a string, received {type(question).__name__}."
            )

        prepared = question.strip()

        if not prepared:
            raise ValueError("Question cannot be empty.")

        return prepared

    @staticmethod
    def _build_sources(
        retrieval_result: RetrievalResult,
    ) -> list[RAGSource]:
        """
        Build API-friendly source information.
        """

        sources: list[RAGSource] = []

        for index, chunk in enumerate(
            retrieval_result.chunks,
            start=1,
        ):
            sources.append(
                RAGSource(
                    number=index,
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    score=chunk.score,
                    content_preview=(RAGService._create_preview(chunk.content)),
                )
            )

        return sources

    @staticmethod
    def _create_preview(
        content: str,
        maximum_characters: int = 240,
    ) -> str:
        """
        Create a short source preview.
        """

        normalized = " ".join(content.split())

        if len(normalized) <= maximum_characters:
            return normalized

        return normalized[:maximum_characters].rstrip() + "..."

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
