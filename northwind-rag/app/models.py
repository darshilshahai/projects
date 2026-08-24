from typing import Literal

from pydantic import BaseModel, Field

RefusalGate = Literal["distance_threshold", "llm_grounding"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    index: int
    source: str
    chunk_index: int
    text: str
    distance: float
    rerank_score: float | None = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class AskResponse(BaseModel):
    answer: str
    refused: bool
    refused_by: RefusalGate | None
    gate_distance: float | None = None
    sources: list[Source]
    usage: Usage | None
    latency_ms: int


class DocumentTextRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=100_000)


class DocumentUploadResponse(BaseModel):
    source: str
    chunks_added: int
    total_chunks: int


class DocumentsListResponse(BaseModel):
    documents: list[str]
    total_chunks: int
