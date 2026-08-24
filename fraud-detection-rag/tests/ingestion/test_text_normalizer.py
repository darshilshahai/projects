from __future__ import annotations


from app.ingestion.processors import TextNormalizer


class TestTextNormalizer:
    def test_returns_empty_string_for_empty_input(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        assert normalizer.normalize("") == ""

    def test_normalizes_windows_line_endings(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "First\r\nSecond\r\nThird"

        assert normalizer.normalize(text) == "First\nSecond\nThird"

    def test_normalizes_legacy_mac_line_endings(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "First\rSecond\rThird"

        assert normalizer.normalize(text) == "First\nSecond\nThird"

    def test_removes_trailing_line_whitespace(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "First line   \nSecond line\t"

        assert normalizer.normalize(text) == "First line\nSecond line"

    def test_collapses_excessive_blank_lines(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "First\n\n\n\n\nSecond"

        assert normalizer.normalize(text) == "First\n\nSecond"

    def test_preserves_single_line_breaks(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "Heading\nFirst line\nSecond line"

        assert normalizer.normalize(text) == text

    def test_preserves_paragraph_boundaries(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "First paragraph.\n\nSecond paragraph."

        assert normalizer.normalize(text) == text

    def test_replaces_non_breaking_spaces(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "Health\u00a0Insurance"

        assert normalizer.normalize(text) == "Health Insurance"

    def test_removes_zero_width_characters(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "Fraud\u200bDetection\ufeffSystem"

        assert normalizer.normalize(text) == "FraudDetectionSystem"

    def test_strips_outer_whitespace(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "   \nPolicy content.\n   "

        assert normalizer.normalize(text) == "Policy content."

    def test_does_not_lowercase_text(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "Health Insurance POLICY"

        assert normalizer.normalize(text) == text

    def test_does_not_remove_punctuation(
        self,
        normalizer: TextNormalizer,
    ) -> None:
        text = "Approved? No! Review claim #123."

        assert normalizer.normalize(text) == text
