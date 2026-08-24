from __future__ import annotations


from app.ingestion import ChunkConfig
from app.ingestion.chunkers import ParagraphChunker


class TestParagraphChunker:
    def test_returns_empty_list_for_empty_text(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        assert paragraph_chunker.split("") == []

    def test_returns_single_short_paragraph(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        text = "Hospital expenses are covered."

        assert paragraph_chunker.split(text) == [text]

    def test_combines_paragraphs_when_they_fit(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        text = "First paragraph.\n\nSecond paragraph."

        assert paragraph_chunker.split(text) == [text]

    def test_splits_paragraphs_when_combined_size_exceeds_target(
        self,
    ) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=20,
            min_chunk_size=10,
        )

        chunker = ParagraphChunker(config)

        first = "A" * 60
        second = "B" * 60
        text = f"{first}\n\n{second}"

        result = chunker.split(text)

        assert result == [first, second]

    def test_supports_blank_lines_containing_spaces(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        text = "First paragraph.\n   \nSecond paragraph."

        result = paragraph_chunker.split(text)

        assert result == ["First paragraph.\n\nSecond paragraph."]

    def test_splits_oversized_paragraph_by_sentences(self) -> None:
        config = ChunkConfig(
            target_size=70,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = ParagraphChunker(config)

        text = (
            "Duplicate invoices should be reviewed. "
            "Provider history should also be checked. "
            "Suspicious claims require investigation."
        )

        result = chunker.split(text)

        assert len(result) >= 2
        assert all(len(segment) <= config.target_size for segment in result)
        assert all(segment.strip() for segment in result)
        assert "Duplicate invoices should be reviewed." in result[0]

    def test_splits_oversized_sentence_by_words(self) -> None:
        config = ChunkConfig(
            target_size=60,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = ParagraphChunker(config)

        text = " ".join(["investigation"] * 30)

        result = chunker.split(text)

        assert len(result) > 1
        assert all(len(segment) <= config.target_size for segment in result)
        assert all(
            " " not in segment or not segment.startswith(" ") for segment in result
        )

    def test_splits_oversized_single_token_by_characters(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=20,
            min_chunk_size=10,
        )

        chunker = ParagraphChunker(config)

        text = "A" * 250

        result = chunker.split(text)

        assert [len(segment) for segment in result] == [
            100,
            100,
            50,
        ]

    def test_merges_small_final_segment_when_it_fits(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=10,
            min_chunk_size=20,
        )

        chunker = ParagraphChunker(config)

        first = "A" * 70
        second = "B" * 10

        result = chunker.split(f"{first}\n\n{second}")

        assert result == [f"{first}\n\n{second}"]

    def test_does_not_merge_small_final_segment_when_target_would_be_exceeded(
        self,
    ) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=10,
            min_chunk_size=20,
        )

        chunker = ParagraphChunker(config)

        first = "A" * 95
        second = "B" * 10

        result = chunker.split(f"{first}\n\n{second}")

        assert result == [first, second]

    def test_preserves_content_order(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        result = paragraph_chunker.split(text)
        reconstructed = "\n\n".join(result)

        assert reconstructed == text

    def test_never_returns_empty_segments(
        self,
        paragraph_chunker: ParagraphChunker,
    ) -> None:
        text = "\n\nFirst paragraph.\n\n\n\nSecond paragraph.\n\n"

        result = paragraph_chunker.split(text)

        assert result
        assert all(segment.strip() for segment in result)
