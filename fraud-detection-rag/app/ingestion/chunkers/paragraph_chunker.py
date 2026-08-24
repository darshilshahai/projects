from __future__ import annotations

import re

from app.ingestion.chunkers.base_chunker import BaseChunker


class ParagraphChunker(BaseChunker):
    """
    Split normalized text while preserving paragraph boundaries.

    The chunker greedily combines neighbouring paragraphs until adding
    another paragraph would exceed the configured target size.

    A paragraph that is individually larger than the target size cannot be
    safely handled by paragraph boundaries alone. Such paragraphs are split
    using a conservative fallback strategy:

        sentence boundary
            ↓
        word boundary
            ↓
        character boundary

    This prevents a single oversized paragraph from producing an extremely
    large chunk.
    """

    _PARAGRAPH_SEPARATOR_PATTERN = re.compile(r"\n\s*\n+")
    _SENTENCE_BOUNDARY_PATTERN = re.compile(r"(?<=[.!?])\s+")

    def split(self, text: str) -> list[str]:
        """
        Split normalized text into paragraph-oriented segments.

        Processing steps:

        1. Validate and prepare input text.
        2. Separate the text into paragraphs.
        3. Greedily combine paragraphs up to target_size.
        4. Split oversized individual paragraphs using fallback boundaries.
        5. Apply shared final cleanup from BaseChunker.

        Args:
            text:
                Normalized source text.

        Returns:
            Ordered paragraph-oriented text segments.

        Raises:
            TypeError:
                When text is not a string.
        """

        prepared_text = self._prepare_text(text)

        if not prepared_text:
            return []

        paragraphs = self._split_into_paragraphs(prepared_text)

        if not paragraphs:
            return []

        segments: list[str] = []
        current_paragraphs: list[str] = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            if paragraph_size > self.config.target_size:
                if current_paragraphs:
                    segments.append(self._join_paragraphs(current_paragraphs))
                    current_paragraphs = []
                    current_size = 0

                oversized_segments = self._split_oversized_paragraph(paragraph)
                segments.extend(oversized_segments)
                continue

            separator_size = 2 if current_paragraphs else 0
            candidate_size = current_size + separator_size + paragraph_size

            if candidate_size <= self.config.target_size:
                current_paragraphs.append(paragraph)
                current_size = candidate_size
                continue

            if current_paragraphs:
                segments.append(self._join_paragraphs(current_paragraphs))

            current_paragraphs = [paragraph]
            current_size = paragraph_size

        if current_paragraphs:
            segments.append(self._join_paragraphs(current_paragraphs))

        segments = self._merge_small_final_segment(segments)

        return self._finalize_segments(segments)

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """
        Split text using one or more blank lines as paragraph boundaries.

        The text normalizer usually reduces excessive blank lines to exactly
        two line breaks, but this method remains defensive and accepts spaces
        or tabs on otherwise blank lines.

        Example:

            "Paragraph one.\\n\\nParagraph two."

        becomes:

            [
                "Paragraph one.",
                "Paragraph two.",
            ]
        """

        raw_paragraphs = self._PARAGRAPH_SEPARATOR_PATTERN.split(text)

        paragraphs: list[str] = []

        for paragraph in raw_paragraphs:
            prepared = paragraph.strip() if self.config.strip_chunks else paragraph

            if self.config.drop_empty_chunks and not prepared.strip():
                continue

            paragraphs.append(prepared)

        return paragraphs

    def _split_oversized_paragraph(
        self,
        paragraph: str,
    ) -> list[str]:
        """
        Split a paragraph that exceeds target_size.

        Paragraph boundaries are unavailable because the entire input is one
        paragraph. The method therefore tries progressively weaker boundaries:

        1. Sentence boundaries
        2. Word boundaries
        3. Character boundaries

        This behaviour keeps the ParagraphChunker safe without turning it into
        a full recursive chunking strategy.
        """

        if len(paragraph) <= self.config.target_size:
            return [paragraph]

        sentences = self._split_into_sentences(paragraph)

        if len(sentences) > 1:
            return self._pack_units(
                units=sentences,
                separator=" ",
            )

        words = paragraph.split()

        if len(words) > 1:
            return self._pack_units(
                units=words,
                separator=" ",
            )

        return self._split_by_characters(paragraph)

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text using common sentence-ending punctuation.

        This is intentionally lightweight. It handles many standard English
        sentences but is not a complete natural-language sentence tokenizer.

        More advanced sentence segmentation can later be added using spaCy,
        syntok, or BlingFire when the corpus requires it.
        """

        sentences = self._SENTENCE_BOUNDARY_PATTERN.split(text)

        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _pack_units(
        self,
        *,
        units: list[str],
        separator: str,
    ) -> list[str]:
        """
        Greedily combine smaller units into target-sized segments.

        Units may be sentences or words.

        A unit that is itself larger than target_size is split at the
        character level to guarantee that the configured maximum is respected.
        """

        segments: list[str] = []
        current_units: list[str] = []
        current_size = 0

        for unit in units:
            if not unit:
                continue

            unit_size = len(unit)

            if unit_size > self.config.target_size:
                if current_units:
                    segments.append(separator.join(current_units))
                    current_units = []
                    current_size = 0

                segments.extend(self._split_by_characters(unit))
                continue

            separator_size = len(separator) if current_units else 0
            candidate_size = current_size + separator_size + unit_size

            if candidate_size <= self.config.target_size:
                current_units.append(unit)
                current_size = candidate_size
                continue

            if current_units:
                segments.append(separator.join(current_units))

            current_units = [unit]
            current_size = unit_size

        if current_units:
            segments.append(separator.join(current_units))

        return segments

    def _split_by_characters(
        self,
        text: str,
    ) -> list[str]:
        """
        Split text into fixed-size character windows.

        This is the final safety fallback. It may split words, so it is used
        only when no stronger boundary is available.
        """

        target_size = self.config.target_size

        return [
            text[start : start + target_size]
            for start in range(0, len(text), target_size)
        ]

    def _merge_small_final_segment(
        self,
        segments: list[str],
    ) -> list[str]:
        """
        Merge an undersized final segment into its predecessor when possible.

        Example with target_size=1000 and min_chunk_size=100:

            [
                chunk of size 850,
                chunk of size 40,
            ]

        The final 40-character chunk is usually weak for retrieval. It is
        merged into the previous chunk only when the combined text does not
        exceed target_size.

        This is intentionally conservative. We do not violate target_size
        merely to satisfy min_chunk_size.
        """

        if len(segments) < 2:
            return segments

        final_segment = segments[-1]

        if len(final_segment) >= self.config.min_chunk_size:
            return segments

        previous_segment = segments[-2]
        combined = f"{previous_segment}\n\n{final_segment}"

        if len(combined) > self.config.target_size:
            return segments

        return [
            *segments[:-2],
            combined,
        ]

    @staticmethod
    def _join_paragraphs(paragraphs: list[str]) -> str:
        """
        Join paragraphs while preserving visible paragraph boundaries.
        """

        return "\n\n".join(paragraphs)
