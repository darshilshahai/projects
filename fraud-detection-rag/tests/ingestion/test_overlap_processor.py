from __future__ import annotations

import pytest

from app.ingestion import ChunkConfig
from app.ingestion.overlap import OverlapProcessor


class TestOverlapProcessor:
    def test_returns_empty_list_for_empty_input(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        assert overlap_processor.apply([]) == []

    def test_rejects_single_string(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        with pytest.raises(TypeError, match="single string"):
            overlap_processor.apply("invalid")  # type: ignore[arg-type]

    def test_rejects_non_string_segment(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        with pytest.raises(TypeError, match="item 1"):
            overlap_processor.apply(
                ["Valid segment.", 123]  # type: ignore[list-item]
            )

    def test_single_segment_is_unchanged(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = ["Single segment."]

        assert overlap_processor.apply(segments) == segments

    def test_first_segment_is_unchanged(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = [
            "First segment has contextual information.",
            "Second segment contains primary information.",
        ]

        result = overlap_processor.apply(segments)

        assert result[0] == segments[0]

    def test_adds_overlap_to_second_segment(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = [
            "Duplicate invoices should trigger additional investigation.",
            "Provider history should also be reviewed.",
        ]

        result = overlap_processor.apply(segments)

        assert result[1].endswith(segments[1])
        assert len(result[1]) > len(segments[1])

    def test_does_not_modify_original_collection(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = [
            "First original segment.",
            "Second original segment.",
        ]

        original_copy = segments.copy()

        overlap_processor.apply(segments)

        assert segments == original_copy

    def test_overlap_does_not_cascade(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = [
            "Alpha context appears only in the first segment.",
            "Beta context only.",
            "Gamma content appears in the third segment.",
        ]

        result = overlap_processor.apply(segments)

        assert "Beta context" in result[2]
        assert "Alpha context" not in result[2]

    def test_overlap_zero_returns_equivalent_copy(
        self,
        no_overlap_config: ChunkConfig,
    ) -> None:
        processor = OverlapProcessor(no_overlap_config)

        segments = [
            "First segment.",
            "Second segment.",
        ]

        result = processor.apply(segments)

        assert result == segments
        assert result is not segments

    def test_removes_empty_segments_when_configured(
        self,
        overlap_processor: OverlapProcessor,
    ) -> None:
        segments = [
            "First segment.",
            "",
            "   ",
            "Second segment.",
        ]

        result = overlap_processor.apply(segments)

        assert len(result) == 2
        assert all(segment.strip() for segment in result)

    def test_output_never_exceeds_target_size(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=50,
            min_chunk_size=10,
        )

        processor = OverlapProcessor(config)

        segments = [
            "A" * 90,
            "B" * 90,
            "C" * 90,
        ]

        result = processor.apply(segments)

        assert all(len(segment) <= config.target_size for segment in result)

    def test_current_segment_receives_priority(self) -> None:
        config = ChunkConfig(
            target_size=100,
            overlap=50,
            min_chunk_size=10,
        )

        processor = OverlapProcessor(config)

        current = "B" * 95

        result = processor.apply(
            [
                "Previous segment has useful context.",
                current,
            ]
        )

        assert result[1].endswith(current)
        assert len(result[1]) <= config.target_size

    def test_uses_trailing_context_not_leading_context(self) -> None:
        config = ChunkConfig(
            target_size=160,
            overlap=35,
            min_chunk_size=10,
        )

        processor = OverlapProcessor(config)

        previous = (
            "Leading content should not be selected. Trailing context is important."
        )

        current = "Current segment."

        result = processor.apply([previous, current])

        assert "Trailing context" in result[1]
        assert result[1].endswith(current)

    def test_character_fallback_handles_unbroken_text(self) -> None:
        config = ChunkConfig(
            target_size=80,
            overlap=20,
            min_chunk_size=10,
        )

        processor = OverlapProcessor(config)

        previous = "A" * 60
        current = "B" * 40

        result = processor.apply([previous, current])

        assert result[1].startswith("A" * 20)
        assert result[1].endswith(current)
        assert len(result[1]) <= config.target_size
