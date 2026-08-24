from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ingestion import Chunk, ChunkConfig, Document


class TestDocument:
    def test_creates_valid_document(self) -> None:
        document = Document(
            content="Valid policy text.",
            source="policy.pdf",
            file_type="pdf",
            metadata={"policy_id": "POL-001"},
        )

        assert document.content == "Valid policy text."
        assert document.source == "policy.pdf"
        assert document.file_type == "pdf"
        assert document.metadata["policy_id"] == "POL-001"

    def test_rejects_empty_content(self) -> None:
        with pytest.raises(ValidationError):
            Document(
                content="",
                source="policy.pdf",
            )

    def test_rejects_whitespace_only_content(self) -> None:
        with pytest.raises(ValidationError):
            Document(
                content="   \n\t ",
                source="policy.pdf",
            )

    def test_rejects_empty_source(self) -> None:
        with pytest.raises(ValidationError):
            Document(
                content="Valid text.",
                source="   ",
            )

    def test_normalizes_source(self) -> None:
        document = Document(
            content="Valid text.",
            source="  policy.pdf  ",
        )

        assert document.source == "policy.pdf"

    @pytest.mark.parametrize(
        ("supplied", "expected"),
        [
            ("PDF", "pdf"),
            (".PDF", "pdf"),
            (" txt ", "txt"),
            (".Markdown", "markdown"),
            ("", None),
            ("   ", None),
            (None, None),
        ],
    )
    def test_normalizes_file_type(
        self,
        supplied: str | None,
        expected: str | None,
    ) -> None:
        document = Document(
            content="Valid text.",
            source="document",
            file_type=supplied,
        )

        assert document.file_type == expected

    def test_uses_independent_metadata_dictionaries(self) -> None:
        first = Document(
            content="First.",
            source="first.txt",
        )

        second = Document(
            content="Second.",
            source="second.txt",
        )

        first.metadata["value"] = "changed"

        assert second.metadata == {}

    def test_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            Document(
                content="Valid text.",
                source="policy.pdf",
                unknown_field="invalid",
            )


class TestChunk:
    def test_creates_valid_chunk(self) -> None:
        chunk = Chunk(
            chunk_id="chunk-001",
            chunk_index=0,
            content="Valid chunk text.",
            source="policy.pdf",
            metadata={"page": 1},
        )

        assert chunk.chunk_id == "chunk-001"
        assert chunk.chunk_index == 0
        assert chunk.content == "Valid chunk text."
        assert chunk.source == "policy.pdf"
        assert chunk.metadata["page"] == 1

    def test_rejects_negative_chunk_index(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(
                chunk_id="chunk-001",
                chunk_index=-1,
                content="Valid chunk text.",
                source="policy.pdf",
            )

    def test_rejects_empty_content(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(
                chunk_id="chunk-001",
                chunk_index=0,
                content="   ",
                source="policy.pdf",
            )

    def test_rejects_empty_chunk_id(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(
                chunk_id=" ",
                chunk_index=0,
                content="Valid text.",
                source="policy.pdf",
            )

    def test_rejects_empty_source(self) -> None:
        with pytest.raises(ValidationError):
            Chunk(
                chunk_id="chunk-001",
                chunk_index=0,
                content="Valid text.",
                source=" ",
            )


class TestChunkConfig:
    def test_creates_valid_default_config(self) -> None:
        config = ChunkConfig()

        assert config.target_size == 1000
        assert config.overlap == 150
        assert config.min_chunk_size == 100
        assert config.separators[-1] == ""

    def test_rejects_overlap_equal_to_target_size(self) -> None:
        with pytest.raises(ValidationError):
            ChunkConfig(
                target_size=200,
                overlap=200,
                min_chunk_size=30,
            )

    def test_rejects_overlap_larger_than_target_size(self) -> None:
        with pytest.raises(ValidationError):
            ChunkConfig(
                target_size=200,
                overlap=201,
                min_chunk_size=30,
            )

    def test_rejects_minimum_size_larger_than_target(self) -> None:
        with pytest.raises(ValidationError):
            ChunkConfig(
                target_size=200,
                overlap=40,
                min_chunk_size=201,
            )

    def test_rejects_duplicate_separators(self) -> None:
        with pytest.raises(ValidationError):
            ChunkConfig(
                target_size=200,
                overlap=40,
                min_chunk_size=30,
                separators=(
                    "\n\n",
                    "\n\n",
                    " ",
                    "",
                ),
            )

    def test_requires_character_fallback_to_be_last(self) -> None:
        with pytest.raises(ValidationError):
            ChunkConfig(
                target_size=200,
                overlap=40,
                min_chunk_size=30,
                separators=(
                    "\n\n",
                    "",
                    " ",
                ),
            )

    def test_config_is_immutable(self) -> None:
        config = ChunkConfig(
            target_size=200,
            overlap=40,
            min_chunk_size=30,
        )

        with pytest.raises(ValidationError):
            config.target_size = 500
