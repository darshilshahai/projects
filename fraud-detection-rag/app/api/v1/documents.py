from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.dependencies import (
    get_chunking_pipeline,
    get_embedder,
    get_vector_store,
)
from app.embeddings.base_embedder import BaseEmbedder
from app.ingestion.pipeline import ChunkingPipeline
from app.ingestion.schemas import Document
from app.vectorstores.chroma_vector_store import ChromaVectorStore


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


class DocumentIngestRequest(BaseModel):
    """
    Request used to ingest one text document.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Complete extracted document text.",
    )

    source: str = Field(
        ...,
        min_length=1,
        description="Stable source document identifier.",
    )

    file_type: str | None = Field(
        default=None,
        description="Source file type.",
    )

    tenant_id: str = Field(
        ...,
        min_length=1,
        description="Tenant that owns the document.",
    )

    category: str | None = Field(
        default=None,
        description="Document category.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source metadata.",
    )

    @field_validator(
        "content",
        "source",
        "tenant_id",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        prepared = value.strip()

        if not prepared:
            raise ValueError("Required text value cannot be empty.")

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


class IngestedChunkSummary(BaseModel):
    chunk_id: str
    chunk_index: int
    content_size: int


class DocumentIngestResponse(BaseModel):
    success: bool = True
    source: str
    tenant_id: str
    chunks_created: int
    vectors_stored: int
    collection_count: int
    chunks: list[IngestedChunkSummary]


@router.post(
    "/ingest",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a text document",
)
def ingest_document(
    request: DocumentIngestRequest,
    chunking_pipeline: ChunkingPipeline = Depends(get_chunking_pipeline),
    embedder: BaseEmbedder = Depends(get_embedder),
    vector_store: ChromaVectorStore = Depends(get_vector_store),
) -> DocumentIngestResponse:
    """
    Chunk, embed, and store one text document.
    """

    document_metadata = {
        **request.metadata,
        "tenant_id": request.tenant_id,
    }

    if request.category is not None:
        document_metadata["category"] = request.category

    document = Document(
        content=request.content,
        source=request.source,
        file_type=request.file_type,
        metadata=document_metadata,
    )

    chunks = chunking_pipeline.process(
        document,
        additional_metadata={
            "ingestion_source": "api",
        },
    )

    if not chunks:
        return DocumentIngestResponse(
            source=document.source,
            tenant_id=request.tenant_id,
            chunks_created=0,
            vectors_stored=0,
            collection_count=vector_store.count(),
            chunks=[],
        )

    embedding_batch = embedder.embed_chunks(chunks)

    vectors_stored = vector_store.upsert(embedding_batch)

    return DocumentIngestResponse(
        source=document.source,
        tenant_id=request.tenant_id,
        chunks_created=len(chunks),
        vectors_stored=vectors_stored,
        collection_count=vector_store.count(),
        chunks=[
            IngestedChunkSummary(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                content_size=len(chunk.content),
            )
            for chunk in chunks
        ],
    )
