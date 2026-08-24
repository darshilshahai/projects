from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api.exception_handlers import (
    register_exception_handlers,
)
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.embeddings import (
    EmbeddingConfig,
    SentenceTransformerEmbedder,
)
from app.ingestion import (
    ChunkConfig,
    ChunkingPipeline,
)
from app.ingestion.chunkers import RecursiveChunker
from app.llm import (
    LLMConfig,
    OpenAILLM,
)
from app.retrieval import (
    RetrievalConfig,
    SemanticRetriever,
)
from app.services import RAGService
from app.vectorstores import (
    ChromaVectorStore,
    VectorStoreConfig,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Initialize expensive shared services once.
    """

    settings = get_settings()

    # ---------------------------------------------------------
    # Chunking
    # ---------------------------------------------------------

    chunk_config = ChunkConfig(
        target_size=settings.chunk_target_size,
        overlap=settings.chunk_overlap,
        min_chunk_size=settings.chunk_minimum_size,
    )

    chunking_pipeline = ChunkingPipeline(
        chunker=RecursiveChunker(chunk_config),
        strategy_name="recursive",
        pipeline_version=settings.app_version,
    )

    # ---------------------------------------------------------
    # Embeddings
    # ---------------------------------------------------------

    embedding_config = EmbeddingConfig(
        model_name=settings.embedding_model_name,
        batch_size=settings.embedding_batch_size,
        normalize_embeddings=settings.normalize_embeddings,
        device=settings.embedding_device,
        show_progress_bar=False,
    )

    embedder = SentenceTransformerEmbedder(embedding_config)

    # Warm up the local embedding model during startup.
    # This prevents the first user query from paying initialization cost.
    embedder.embed_query("embedding model warmup")

    # ---------------------------------------------------------
    # Vector store
    # ---------------------------------------------------------

    vector_store = ChromaVectorStore(
        VectorStoreConfig(
            persist_directory=(settings.chroma_persist_directory),
            collection_name=(settings.chroma_collection_name),
            distance_metric=(settings.chroma_distance_metric),
            expected_dimension=embedder.dimension,
        )
    )

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    retrieval_config = RetrievalConfig(
        top_k=settings.retrieval_top_k,
        fetch_k=settings.retrieval_fetch_k,
        minimum_score=(settings.retrieval_minimum_score),
        maximum_context_characters=(settings.retrieval_maximum_context_characters),
        remove_duplicate_content=True,
        remove_near_duplicate_content=True,
        near_duplicate_similarity_threshold=(
            settings.retrieval_near_duplicate_threshold
        ),
        include_metadata=True,
    )

    retriever = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
        config=retrieval_config,
    )

    # ---------------------------------------------------------
    # LLM
    # ---------------------------------------------------------

    llm = OpenAILLM(
        LLMConfig(
            model_name=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            max_output_tokens=(settings.llm_max_output_tokens),
            timeout_seconds=(settings.llm_timeout_seconds),
            max_retries=settings.llm_max_retries,
        )
    )

    # ---------------------------------------------------------
    # RAG service
    # ---------------------------------------------------------

    rag_service = RAGService(
        retriever=retriever,
        llm=llm,
    )

    app.state.chunking_pipeline = chunking_pipeline
    app.state.embedder = embedder
    app.state.vector_store = vector_store
    app.state.rag_service = rag_service

    yield

    app.state.chunking_pipeline = None
    app.state.embedder = None
    app.state.vector_store = None
    app.state.rag_service = None


def create_application() -> FastAPI:
    """
    Create the FastAPI application.
    """

    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @application.middleware("http")
    async def add_process_time_header(
        request: Request,
        call_next: Callable[
            [Request],
            Awaitable[Response],
        ],
    ) -> Response:
        """
        Measure full server-side HTTP processing time.
        """

        started_at = time.perf_counter()

        response = await call_next(request)

        process_time_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        response.headers["X-Process-Time-Ms"] = str(process_time_ms)

        return response

    application.include_router(
        api_v1_router,
        prefix=settings.api_v1_prefix,
    )

    register_exception_handlers(application)

    return application


app = create_application()