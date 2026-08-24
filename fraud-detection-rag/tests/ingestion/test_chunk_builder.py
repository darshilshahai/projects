from __future__ import annotations

import pytest

from app.ingestion import Document
from app.ingestion.builders import ChunkBuilder


class TestChunkBuilder:
    def test_builds_multiple_chunks(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        chunks = chunk_builder.build_many(
            document=document,
            segments=[
                "First segment.",
                "Second segment.",
            ],
            strategy="recursive",
        )

        assert len(chunks) == 2
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1
        assert chunks[0].content == "First segment."
        assert chunks[1].content == "Second segment."

    def test_returns_empty_list_for_empty_segments(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        assert (
            chunk_builder.build_many(
                document=document,
                segments=[],
                strategy="recursive",
            )
            == []
        )

    def test_rejects_single_string(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        with pytest.raises(TypeError, match="single string"):
            chunk_builder.build_many(
                document=document,
                segments="invalid",  # type: ignore[arg-type]
                strategy="recursive",
            )

    def test_rejects_non_string_segment(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        with pytest.raises(TypeError, match="item 1"):
            chunk_builder.build_many(
                document=document,
                segments=[
                    "Valid segment.",
                    123,  # type: ignore[list-item]
                ],
                strategy="recursive",
            )

    def test_removes_empty_segments(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        chunks = chunk_builder.build_many(
            document=document,
            segments=[
                "First segment.",
                "",
                "   ",
                "Second segment.",
            ],
            strategy="recursive",
        )

        assert len(chunks) == 2
        assert [chunk.chunk_index for chunk in chunks] == [0, 1]

    def test_normalizes_strategy_name(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        chunks = chunk_builder.build_many(
            document=document,
            segments=["Content."],
            strategy=" RECURSIVE ",
        )

        assert chunks[0].metadata["chunking_strategy"] == "recursive"

    def test_rejects_empty_strategy(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            chunk_builder.build_many(
                document=document,
                segments=["Content."],
                strategy="   ",
            )

    def test_generates_deterministic_ids(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        first = chunk_builder.build_many(
            document=document,
            segments=["Stable content."],
            strategy="recursive",
        )

        second = chunk_builder.build_many(
            document=document,
            segments=["Stable content."],
            strategy="recursive",
        )

        assert first[0].chunk_id == second[0].chunk_id
        assert len(first[0].chunk_id) == 64

    def test_changed_content_changes_id(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        first = chunk_builder.build_one(
            document=document,
            content="Claim deadline is 30 days.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
        )

        second = chunk_builder.build_one(
            document=document,
            content="Claim deadline is 45 days.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
        )

        assert first.chunk_id != second.chunk_id

    def test_changed_source_changes_id(
        self,
        chunk_builder: ChunkBuilder,
    ) -> None:
        first_document = Document(
            content="Source document.",
            source="first.pdf",
        )

        second_document = Document(
            content="Source document.",
            source="second.pdf",
        )

        first = chunk_builder.build_one(
            document=first_document,
            content="Identical chunk content.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
        )

        second = chunk_builder.build_one(
            document=second_document,
            content="Identical chunk content.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
        )

        assert first.chunk_id != second.chunk_id

    def test_changed_index_changes_id(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        first = chunk_builder.build_one(
            document=document,
            content="Repeated content.",
            chunk_index=0,
            total_chunks=2,
            strategy="recursive",
        )

        second = chunk_builder.build_one(
            document=document,
            content="Repeated content.",
            chunk_index=1,
            total_chunks=2,
            strategy="recursive",
        )

        assert first.chunk_id != second.chunk_id

    def test_changed_strategy_changes_id(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        recursive = chunk_builder.build_one(
            document=document,
            content="Same content.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
        )

        paragraph = chunk_builder.build_one(
            document=document,
            content="Same content.",
            chunk_index=0,
            total_chunks=1,
            strategy="paragraph",
        )

        assert recursive.chunk_id != paragraph.chunk_id

    def test_builds_expected_metadata(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        chunks = chunk_builder.build_many(
            document=document,
            segments=[
                "First.",
                "Second.",
            ],
            strategy="recursive",
            additional_metadata={
                "pipeline_version": "1.0.0",
            },
        )

        first = chunks[0]
        second = chunks[1]

        assert first.metadata["document_id"] == "DOC-001"
        assert first.metadata["pipeline_version"] == "1.0.0"
        assert first.metadata["file_type"] == "pdf"
        assert first.metadata["chunk_index"] == 0
        assert first.metadata["chunk_number"] == 1
        assert first.metadata["total_chunks"] == 2
        assert first.metadata["chunk_size"] == len(first.content)
        assert first.metadata["is_first_chunk"] is True
        assert first.metadata["is_last_chunk"] is False

        assert second.metadata["is_first_chunk"] is False
        assert second.metadata["is_last_chunk"] is True

    def test_protected_metadata_cannot_be_overridden(
        self,
        chunk_builder: ChunkBuilder,
    ) -> None:
        document = Document(
            content="Document.",
            source="policy.pdf",
            metadata={
                "chunk_index": 999,
                "chunk_size": 999,
                "total_chunks": 999,
            },
        )

        chunk = chunk_builder.build_one(
            document=document,
            content="Actual content.",
            chunk_index=0,
            total_chunks=1,
            strategy="recursive",
            additional_metadata={
                "chunk_index": 500,
                "chunk_size": 500,
            },
        )

        assert chunk.metadata["chunk_index"] == 0
        assert chunk.metadata["chunk_size"] == len("Actual content.")
        assert chunk.metadata["total_chunks"] == 1

    def test_does_not_mutate_additional_metadata(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
    ) -> None:
        metadata = {
            "pipeline_version": "1.0.0",
        }

        original = metadata.copy()

        chunk_builder.build_many(
            document=document,
            segments=["Content."],
            strategy="recursive",
            additional_metadata=metadata,
        )

        assert metadata == original

    @pytest.mark.parametrize(
        ("chunk_index", "total_chunks", "error"),
        [
            (-1, 1, "cannot be negative"),
            (0, 0, "greater than zero"),
            (1, 1, "smaller than"),
        ],
    )
    def test_rejects_invalid_index_values(
        self,
        chunk_builder: ChunkBuilder,
        document: Document,
        chunk_index: int,
        total_chunks: int,
        error: str,
    ) -> None:
        with pytest.raises(ValueError, match=error):
            chunk_builder.build_one(
                document=document,
                content="Content.",
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                strategy="recursive",
            )
