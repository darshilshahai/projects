from __future__ import annotations

import pytest

from app.ingestion import ChunkConfig, Document
from app.ingestion.builders import ChunkBuilder
from app.ingestion.chunkers import ParagraphChunker, RecursiveChunker
from app.ingestion.overlap import OverlapProcessor
from app.ingestion.processors import TextNormalizer


@pytest.fixture
def chunk_config() -> ChunkConfig:
    """
    Return a small configuration suitable for deterministic unit tests.
    """

    return ChunkConfig(
        target_size=200,
        overlap=40,
        min_chunk_size=30,
    )


@pytest.fixture
def no_overlap_config() -> ChunkConfig:
    """
    Return a configuration with overlap disabled.
    """

    return ChunkConfig(
        target_size=200,
        overlap=0,
        min_chunk_size=30,
    )


@pytest.fixture
def document() -> Document:
    """
    Return a representative insurance document.
    """

    return Document(
        content=(
            "Health Insurance Fraud Guidelines\r\n"
            "\r\n"
            "\r\n"
            "Duplicate invoices may indicate repeated billing.   \r\n"
            "\r\n"
            "Investigators should compare provider details, "
            "treatment dates, invoice numbers, and billed amounts."
        ),
        source="data/fraud-guidelines.pdf",
        file_type=".PDF",
        metadata={
            "document_id": "DOC-001",
            "tenant_id": "INSURER-001",
            "category": "fraud-guideline",
        },
    )


@pytest.fixture
def normalizer() -> TextNormalizer:
    return TextNormalizer()


@pytest.fixture
def paragraph_chunker(
    chunk_config: ChunkConfig,
) -> ParagraphChunker:
    return ParagraphChunker(chunk_config)


@pytest.fixture
def recursive_chunker(
    chunk_config: ChunkConfig,
) -> RecursiveChunker:
    return RecursiveChunker(chunk_config)


@pytest.fixture
def overlap_processor(
    chunk_config: ChunkConfig,
) -> OverlapProcessor:
    return OverlapProcessor(chunk_config)


@pytest.fixture
def chunk_builder() -> ChunkBuilder:
    return ChunkBuilder()
