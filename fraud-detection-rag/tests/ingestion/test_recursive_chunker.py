from __future__ import annotations


from app.ingestion import ChunkConfig
from app.ingestion.chunkers import RecursiveChunker


class TestRecursiveChunker:
    def test_returns_empty_list_for_empty_text(
        self,
        recursive_chunker: RecursiveChunker,
    ) -> None:
        assert recursive_chunker.split("") == []

    def test_returns_short_text_unchanged(
        self,
        recursive_chunker: RecursiveChunker,
    ) -> None:
        text = "Short policy content."

        assert recursive_chunker.split(text) == [text]

    def test_uses_paragraph_boundary_first(self) -> None:
        config = ChunkConfig(
            target_size=90,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        first = "A" * 60
        second = "B" * 60

        result = chunker.split(f"{first}\n\n{second}")

        assert result == [first, second]

    def test_preserves_paragraph_separator_when_pieces_fit(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        text = "First paragraph.\n\nSecond paragraph."

        assert chunker.split(text) == [text]

    def test_falls_back_to_single_line_separator(self) -> None:
        config = ChunkConfig(
            target_size=50,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        text = "Heading\nFirst line contains details\nSecond line contains details"

        result = chunker.split(text)

        assert len(result) >= 2
        assert all(len(segment) <= config.target_size for segment in result)

    def test_falls_back_to_sentence_separator(self) -> None:
        config = ChunkConfig(
            target_size=65,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        text = (
            "First claim requires review. "
            "Second claim requires investigation. "
            "Third claim requires escalation."
        )

        result = chunker.split(text)

        assert len(result) >= 2
        assert all(len(segment) <= config.target_size for segment in result)

    def test_falls_back_to_word_separator(self) -> None:
        config = ChunkConfig(
            target_size=50,
            overlap=10,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        text = " ".join(["fraud"] * 50)

        result = chunker.split(text)

        assert len(result) > 1
        assert all(len(segment) <= config.target_size for segment in result)

    def test_falls_back_to_character_splitting(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=20,
            min_chunk_size=10,
        )

        chunker = RecursiveChunker(config)

        text = "X" * 250

        result = chunker.split(text)

        assert [len(segment) for segment in result] == [
            100,
            100,
            50,
        ]

    def test_custom_separator_order_is_respected(self) -> None:
        config = ChunkConfig(
            target_size=30,
            overlap=5,
            min_chunk_size=5,
            separators=(
                "|",
                " ",
                "",
            ),
        )

        chunker = RecursiveChunker(config)

        text = "first section content|second section content"

        result = chunker.split(text)

        assert result == [
            "first section content",
            "second section content",
        ]

    def test_merges_small_final_segment_when_possible(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=10,
            min_chunk_size=20,
        )

        chunker = RecursiveChunker(config)

        first = "A" * 70
        second = "B" * 10

        result = chunker.split(f"{first}\n\n{second}")

        assert result == [f"{first}\n\n{second}"]

    def test_never_exceeds_target_size(self) -> None:
        config = ChunkConfig(
            target_size=120,
            overlap=20,
            min_chunk_size=15,
        )

        chunker = RecursiveChunker(config)

        text = (
            ("First paragraph sentence. " * 20)
            + "\n\n"
            + ("Second paragraph sentence. " * 20)
        )

        result = chunker.split(text)

        assert result
        assert all(len(segment) <= config.target_size for segment in result)

    def test_never_returns_empty_segments(
        self,
        recursive_chunker: RecursiveChunker,
    ) -> None:
        text = "\n\nFirst paragraph.\n\n\n\nSecond paragraph.\n\n"

        result = recursive_chunker.split(text)

        assert result
        assert all(segment.strip() for segment in result)

    def test_preserves_logical_content_order(self) -> None:
        config = ChunkConfig(
            target_size=50,
            overlap=10,
            min_chunk_size=5,
        )

        chunker = RecursiveChunker(config)

        text = "Alpha section.\n\nBeta section.\n\nGamma section."

        result = chunker.split(text)
        reconstructed = "\n\n".join(result)

        assert "Alpha section." in reconstructed
        assert reconstructed.index("Alpha") < reconstructed.index("Beta")
        assert reconstructed.index("Beta") < reconstructed.index("Gamma")
