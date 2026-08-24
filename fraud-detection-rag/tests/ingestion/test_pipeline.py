from __future__ import annotations

from typing import Any

import pytest

from app.ingestion import (
    ChunkConfig,
    ChunkingPipeline,
    ChunkingPipelineError,
    Document,
    TextChunkingError,
    TextNormalizationError,
)
from app.ingestion.chunkers import BaseChunker, ParagraphChunker, RecursiveChunker
from app.ingestion.overlap import OverlapProcessor
from app.ingestion.processors import TextNormalizer


class FailingNormalizer(TextNormalizer):
    """
    Test double that always fails during normalization.
    """

    def normalize(self, text: str) -> str:
        raise ValueError("Forced normalization failure.")


class FailingChunker(BaseChunker):
    """
    Test double that always fails during splitting.
    """

    def split(self, text: str) -> list[str]:
        raise ValueError("Forced chunking failure.")


class TestChunkingPipeline:
    def test_processes_document_end_to_end(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
            pipeline_version="1.0.0",
        )

        chunks = pipeline.process(document)

        assert chunks
        assert all(chunk.content.strip() for chunk in chunks)
        assert all(len(chunk.content) <= chunk_config.target_size for chunk in chunks)

        assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))

        assert all(
            chunk.metadata["chunking_strategy"] == "recursive" for chunk in chunks
        )

        assert all(chunk.metadata["pipeline_version"] == "1.0.0" for chunk in chunks)

    def test_pipeline_is_deterministic(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        first_run = pipeline.process(document)
        second_run = pipeline.process(document)

        assert [chunk.chunk_id for chunk in first_run] == [
            chunk.chunk_id for chunk in second_run
        ]

        assert [chunk.content for chunk in first_run] == [
            chunk.content for chunk in second_run
        ]

    def test_supports_paragraph_strategy(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=ParagraphChunker(chunk_config),
            strategy_name="paragraph",
        )

        chunks = pipeline.process(document)

        assert chunks
        assert all(
            chunk.metadata["chunking_strategy"] == "paragraph" for chunk in chunks
        )

    def test_supports_recursive_strategy(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        chunks = pipeline.process(document)

        assert chunks
        assert all(
            chunk.metadata["chunking_strategy"] == "recursive" for chunk in chunks
        )

    def test_adds_pipeline_metadata(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
            pipeline_version="2.1.0",
        )

        chunks = pipeline.process(document)

        metadata = chunks[0].metadata

        assert metadata["pipeline_version"] == "2.1.0"
        assert metadata["target_chunk_size"] == chunk_config.target_size
        assert metadata["minimum_chunk_size"] == chunk_config.min_chunk_size
        assert metadata["requested_overlap"] == chunk_config.overlap
        assert metadata["overlap_enabled"] is True
        assert metadata["source_content_size"] == len(document.content)
        assert metadata["normalized_content_size"] > 0
        assert metadata["segments_before_overlap"] > 0
        assert metadata["segments_after_overlap"] > 0

    def test_adds_caller_metadata(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        chunks = pipeline.process(
            document,
            additional_metadata={
                "ingestion_job_id": "JOB-001",
                "environment": "test",
            },
        )

        assert all(chunk.metadata["ingestion_job_id"] == "JOB-001" for chunk in chunks)

        assert all(chunk.metadata["environment"] == "test" for chunk in chunks)

    def test_pipeline_metadata_overrides_caller_values(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
            pipeline_version="1.0.0",
        )

        chunks = pipeline.process(
            document,
            additional_metadata={
                "pipeline_version": "fake",
                "target_chunk_size": 99999,
                "chunking_strategy": "fake",
            },
        )

        metadata = chunks[0].metadata

        assert metadata["pipeline_version"] == "1.0.0"
        assert metadata["target_chunk_size"] == chunk_config.target_size
        assert metadata["chunking_strategy"] == "recursive"

    def test_does_not_mutate_caller_metadata(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        metadata: dict[str, Any] = {
            "ingestion_job_id": "JOB-001",
        }

        original = metadata.copy()

        pipeline.process(
            document,
            additional_metadata=metadata,
        )

        assert metadata == original

    def test_rejects_empty_strategy_name(
        self,
        chunk_config: ChunkConfig,
    ) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            ChunkingPipeline(
                chunker=RecursiveChunker(chunk_config),
                strategy_name="   ",
            )

    def test_rejects_empty_pipeline_version(
        self,
        chunk_config: ChunkConfig,
    ) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            ChunkingPipeline(
                chunker=RecursiveChunker(chunk_config),
                strategy_name="recursive",
                pipeline_version=" ",
            )

    def test_rejects_mismatched_overlap_config(self) -> None:
        chunker_config = ChunkConfig(
            target_size=200,
            overlap=40,
            min_chunk_size=30,
        )

        overlap_config = ChunkConfig(
            target_size=300,
            overlap=50,
            min_chunk_size=30,
        )

        with pytest.raises(ValueError, match="same ChunkConfig"):
            ChunkingPipeline(
                chunker=RecursiveChunker(chunker_config),
                strategy_name="recursive",
                overlap_processor=OverlapProcessor(overlap_config),
            )

    def test_wraps_normalization_failures(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
            normalizer=FailingNormalizer(),
        )

        with pytest.raises(
            TextNormalizationError,
            match="Failed to normalize",
        ) as error:
            pipeline.process(document)

        assert isinstance(error.value.__cause__, ValueError)

    def test_wraps_chunking_failures(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=FailingChunker(chunk_config),
            strategy_name="failing",
        )

        with pytest.raises(
            TextChunkingError,
            match="failed to split",
        ) as error:
            pipeline.process(document)

        assert isinstance(error.value.__cause__, ValueError)

    def test_stage_exceptions_inherit_from_pipeline_error(self) -> None:
        assert issubclass(
            TextNormalizationError,
            ChunkingPipelineError,
        )

        assert issubclass(
            TextChunkingError,
            ChunkingPipelineError,
        )

    def test_overlap_disabled_pipeline(
        self,
        no_overlap_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(no_overlap_config),
            strategy_name="recursive",
        )

        chunks = pipeline.process(document)

        assert chunks
        assert all(chunk.metadata["overlap_enabled"] is False for chunk in chunks)

        assert all(chunk.metadata["requested_overlap"] == 0 for chunk in chunks)

    def test_output_chunk_metadata_matches_content(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        chunks = pipeline.process(document)

        for chunk in chunks:
            assert chunk.metadata["chunk_size"] == len(chunk.content)
            assert chunk.metadata["chunk_index"] == chunk.chunk_index
            assert chunk.metadata["total_chunks"] == len(chunks)

    def test_first_and_last_chunk_metadata(
        self,
        chunk_config: ChunkConfig,
        document: Document,
    ) -> None:
        pipeline = ChunkingPipeline(
            chunker=RecursiveChunker(chunk_config),
            strategy_name="recursive",
        )

        chunks = pipeline.process(document)

        assert chunks[0].metadata["is_first_chunk"] is True
        assert chunks[0].metadata["chunk_number"] == 1

        assert chunks[-1].metadata["is_last_chunk"] is True
        assert chunks[-1].metadata["chunk_number"] == len(chunks)
