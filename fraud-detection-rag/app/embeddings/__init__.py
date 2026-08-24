"""
Provider-independent embedding subsystem.
"""

from app.embeddings.base_embedder import BaseEmbedder
from app.embeddings.embedding_config import EmbeddingConfig
from app.embeddings.embedding_schema import EmbeddingBatch
from app.embeddings.sentence_transformer_embedder import (
    SentenceTransformerEmbedder,
)

__all__ = [
    "BaseEmbedder",
    "EmbeddingBatch",
    "EmbeddingConfig",
    "SentenceTransformerEmbedder",
]
