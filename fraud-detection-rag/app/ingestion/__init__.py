"""
Document ingestion framework.

The ingestion package provides:

- validated source document models
- text normalization
- configurable chunking strategies
- contextual overlap processing
- deterministic Chunk construction
- pipeline orchestration
"""

from app.ingestion.chunk_config import ChunkConfig
from app.ingestion.chunk_schema import Chunk
from app.ingestion.pipeline import (
    ChunkBuildingError,
    ChunkingPipeline,
    ChunkingPipelineError,
    OverlapProcessingError,
    TextChunkingError,
    TextNormalizationError,
)
from app.ingestion.schemas import Document

__all__ = [
    "Chunk",
    "ChunkConfig",
    "Document",
    "ChunkingPipeline",
    "ChunkingPipelineError",
    "TextNormalizationError",
    "TextChunkingError",
    "OverlapProcessingError",
    "ChunkBuildingError",
]
