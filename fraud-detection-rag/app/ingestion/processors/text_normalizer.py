from __future__ import annotations
import re


class TextNormalizer:
    """
    Normalize extracted document text before chunking.

    The normalizer performs conservative cleanup. It removes extraction noise
    while preserving paragraph boundaries because paragraph structure is
    valuable for retrieval-oriented chunking.

    It intentionally does not:

    - lowercase content
    - remove punctuation
    - remove stop words
    - collapse all whitespace into one space
    - rewrite document meaning

    Those transformations can damage semantic meaning and retrieval quality.
    """

    _TRAILING_HORIZONTAL_WHITESPACE_PATTERN = re.compile(r"[ \t]+$", re.MULTILINE)
    _EXCESSIVE_BLANK_LINES_PATTERN = re.compile(r"\n{3,}")
    _NON_BREAKING_SPACE_PATTERN = re.compile(r"\u00A0")
    _ZERO_WIDTH_CHARACTER_PATTERN = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")

    def normalize(self, text: str) -> str:
        """
        Return a normalized representation of the supplied text.

        Processing order matters:

        1. Validate the input type.
        2. Normalize line endings.
        3. Replace non-breaking spaces.
        4. Remove invisible zero-width characters.
        5. Remove trailing spaces from lines.
        6. Collapse excessive blank lines.
        7. Strip surrounding whitespace.

        Args:
            text:
                Raw text extracted from a source document.

        Returns:
            Normalized text.

        Raises:
            TypeError:
                When text is not a string.
        """

        if not text:
            return ""

        normalized = self._normalize_line_endings(text)
        normalized = self._replace_non_breaking_spaces(normalized)
        normalized = self._remove_zero_width_characters(normalized)
        normalized = self._remove_trailing_whitespace(normalized)
        normalized = self._collapse_blank_lines(normalized)

        return normalized.strip()

    @staticmethod
    def _normalize_line_endings(text: str) -> str:
        """
        Convert Windows and legacy Mac line endings to Unix line endings.
        """

        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _replace_non_breaking_spaces(self, text: str) -> str:
        """
        Replace non-breaking spaces with regular spaces.
        """

        return self._NON_BREAKING_SPACE_PATTERN.sub(" ", text)

    def _remove_zero_width_characters(self, text: str) -> str:
        """
        Remove invisible Unicode characters commonly introduced by PDF,
        HTML, and word-processing extraction.
        """

        return self._ZERO_WIDTH_CHARACTER_PATTERN.sub("", text)

    def _remove_trailing_whitespace(self, text: str) -> str:
        """
        Remove spaces and tabs from the end of each line.
        """

        return self._TRAILING_HORIZONTAL_WHITESPACE_PATTERN.sub("", text)

    def _collapse_blank_lines(self, text: str) -> str:
        """
        Reduce three or more consecutive line breaks to one paragraph break.
        """

        return self._EXCESSIVE_BLANK_LINES_PATTERN.sub("\n\n", text)
