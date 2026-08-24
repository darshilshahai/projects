from __future__ import annotations

from fastapi import Request

from app.ingestion.pipeline import ChunkingPipeline
from app.services.rag_service import RAGService
from app.vectorstores.chroma_vector_store import ChromaVectorStore
from app.embeddings.base_embedder import BaseEmbedder


class ApplicationDependencyError(RuntimeError):
    """
    Raised when a required application service was not initialized.
    """


def get_chunking_pipeline(
    request: Request,
) -> ChunkingPipeline:
    """
    Return the shared ChunkingPipeline from application state.
    """

    pipeline = getattr(
        request.app.state,
        "chunking_pipeline",
        None,
    )

    if not isinstance(pipeline, ChunkingPipeline):
        raise ApplicationDependencyError("Chunking pipeline is not initialized.")

    return pipeline


def get_vector_store(
    request: Request,
) -> ChromaVectorStore:
    """
    Return the shared Chroma vector store.
    """

    vector_store = getattr(
        request.app.state,
        "vector_store",
        None,
    )

    if not isinstance(vector_store, ChromaVectorStore):
        raise ApplicationDependencyError("Vector store is not initialized.")

    return vector_store


def get_rag_service(
    request: Request,
) -> RAGService:
    """
    Return the shared RAGService.
    """

    service = getattr(
        request.app.state,
        "rag_service",
        None,
    )

    if not isinstance(service, RAGService):
        raise ApplicationDependencyError("RAG service is not initialized.")

    return service


def get_embedder(
    request: Request,
) -> BaseEmbedder:
    """
    Return the shared embedding service.
    """

    embedder = getattr(
        request.app.state,
        "embedder",
        None,
    )

    if not isinstance(embedder, BaseEmbedder):
        raise ApplicationDependencyError("Embedding service is not initialized.")

    return embedder
