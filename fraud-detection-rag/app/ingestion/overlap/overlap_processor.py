from __future__ import annotations

import re
from collections.abc import Sequence

from app.ingestion.chunk_config import ChunkConfig


class OverlapProcessor:
    """
    Add contextual overlap between adjacent text segments.

    The processor receives text segments produced by a chunking strategy and
    prepends context from the previous segment to each subsequent segment.

    It prefers semantic boundaries when selecting overlap text:

        1. Complete trailing sentences
        2. Complete trailing words
        3. Character-level fallback

    The first segment is returned without overlap because no previous context
    exists.

    The processor does not:

    - split source documents
    - create Chunk objects
    - generate chunk IDs
    - modify metadata
    - create embeddings
    """

    _SENTENCE_PATTERN = re.compile(
        r".+?(?:[.!?](?=\s|$)|$)",
        re.DOTALL,
    )

    def __init__(self, config: ChunkConfig) -> None:
        """
        Initialize the overlap processor.

        Args:
            config:
                Immutable chunking configuration containing the requested
                overlap size and maximum target size.
        """

        self._config = config

    @property
    def config(self) -> ChunkConfig:
        """
        Return the immutable overlap configuration.
        """

        return self._config

    def apply(self, segments: Sequence[str]) -> list[str]:
        """
        Add overlap from each previous segment to the next segment.

        Args:
            segments:
                Ordered text segments produced by a chunking strategy.

        Returns:
            A new list containing overlap-enhanced segments.

        Raises:
            TypeError:
                When segments is not a sequence of strings or contains a
                non-string item.

        Important:
            The input collection is never modified.
        """

        prepared_segments = self._prepare_segments(segments)

        if not prepared_segments:
            return []

        if self.config.overlap == 0:
            return prepared_segments.copy()

        overlapped_segments: list[str] = [prepared_segments[0]]

        for index in range(1, len(prepared_segments)):
            previous_segment = prepared_segments[index - 1]
            current_segment = prepared_segments[index]

            overlap_text = self._extract_overlap(previous_segment)

            combined = self._combine(
                overlap_text=overlap_text,
                current_segment=current_segment,
            )

            overlapped_segments.append(combined)

        return overlapped_segments

    def _prepare_segments(
        self,
        segments: Sequence[str],
    ) -> list[str]:
        """
        Validate and normalize the input segment collection.

        Empty segments are removed when drop_empty_chunks is enabled.
        Surrounding whitespace is removed when strip_chunks is enabled.
        """

        if isinstance(segments, str):
            raise TypeError(
                "OverlapProcessor expected a sequence of strings, "
                "but received a single string."
            )

        prepared_segments: list[str] = []

        for index, segment in enumerate(segments):
            if not isinstance(segment, str):
                raise TypeError(
                    "OverlapProcessor expected every segment to be a string, "
                    f"but item {index} is {type(segment).__name__}."
                )

            prepared = segment.strip() if self.config.strip_chunks else segment

            if self.config.drop_empty_chunks and not prepared.strip():
                continue

            prepared_segments.append(prepared)

        return prepared_segments

    def _extract_overlap(
        self,
        previous_segment: str,
    ) -> str:
        """
        Extract contextual text from the end of the previous segment.

        The configured overlap is treated as a preferred maximum size.

        Selection hierarchy:

        1. Trailing complete sentences that fit inside overlap.
        2. Trailing complete words that fit inside overlap.
        3. Final overlap characters when no better boundary exists.
        """

        overlap_size = self.config.overlap

        if overlap_size <= 0 or not previous_segment:
            return ""

        if len(previous_segment) <= overlap_size:
            return previous_segment

        sentence_overlap = self._extract_sentence_overlap(
            text=previous_segment,
            maximum_size=overlap_size,
        )

        if sentence_overlap:
            return sentence_overlap

        word_overlap = self._extract_word_overlap(
            text=previous_segment,
            maximum_size=overlap_size,
        )

        if word_overlap:
            return word_overlap

        return previous_segment[-overlap_size:]

    def _extract_sentence_overlap(
        self,
        *,
        text: str,
        maximum_size: int,
    ) -> str:
        """
        Return complete trailing sentences within maximum_size.

        Sentences are accumulated from the end of the segment backwards.
        The method does not return partial sentences.

        If no complete sentence fits, an empty string is returned so the
        processor can fall back to word-level extraction.
        """

        sentences = [
            match.group(0).strip()
            for match in self._SENTENCE_PATTERN.finditer(text)
            if match.group(0).strip()
        ]

        if not sentences:
            return ""

        selected: list[str] = []
        current_size = 0

        for sentence in reversed(sentences):
            separator_size = 1 if selected else 0
            candidate_size = current_size + separator_size + len(sentence)

            if candidate_size > maximum_size:
                break

            selected.append(sentence)
            current_size = candidate_size

        if not selected:
            return ""

        selected.reverse()

        return " ".join(selected)

    @staticmethod
    def _extract_word_overlap(
        *,
        text: str,
        maximum_size: int,
    ) -> str:
        """
        Return complete trailing words within maximum_size.

        Words are accumulated backwards so the most recent context is
        preserved.
        """

        words = text.split()

        if not words:
            return ""

        selected: list[str] = []
        current_size = 0

        for word in reversed(words):
            separator_size = 1 if selected else 0
            candidate_size = current_size + separator_size + len(word)

            if candidate_size > maximum_size:
                break

            selected.append(word)
            current_size = candidate_size

        if not selected:
            return ""

        selected.reverse()

        return " ".join(selected)

    def _combine(
        self,
        *,
        overlap_text: str,
        current_segment: str,
    ) -> str:
        """
        Combine overlap text with the current segment.

        The method guarantees that the final result does not exceed
        target_size. When necessary, the overlap portion is reduced before
        the current segment is touched.

        Current-segment content receives priority because it is the primary
        content assigned to that segment.
        """

        if not overlap_text:
            return current_segment

        separator = self._select_join_separator(
            overlap_text=overlap_text,
            current_segment=current_segment,
        )

        available_overlap_size = (
            self.config.target_size - len(current_segment) - len(separator)
        )

        if available_overlap_size <= 0:
            return current_segment

        if len(overlap_text) > available_overlap_size:
            overlap_text = self._trim_overlap_to_size(
                text=overlap_text,
                maximum_size=available_overlap_size,
            )

        if not overlap_text:
            return current_segment

        combined = f"{overlap_text}{separator}{current_segment}"

        if len(combined) <= self.config.target_size:
            return combined

        # Defensive fallback. The earlier calculations should already ensure
        # the result fits, but the slice guarantees the invariant if custom
        # Unicode or separator behaviour changes in the future.
        overflow = len(combined) - self.config.target_size
        trimmed_overlap = overlap_text[overflow:].lstrip()

        if not trimmed_overlap:
            return current_segment

        return f"{trimmed_overlap}{separator}{current_segment}"

    def _trim_overlap_to_size(
        self,
        *,
        text: str,
        maximum_size: int,
    ) -> str:
        """
        Reduce overlap while preserving the strongest available boundary.

        The method tries:

        1. Complete trailing sentences
        2. Complete trailing words
        3. Character-level tail
        """

        if maximum_size <= 0:
            return ""

        if len(text) <= maximum_size:
            return text

        sentence_overlap = self._extract_sentence_overlap(
            text=text,
            maximum_size=maximum_size,
        )

        if sentence_overlap:
            return sentence_overlap

        word_overlap = self._extract_word_overlap(
            text=text,
            maximum_size=maximum_size,
        )

        if word_overlap:
            return word_overlap

        return text[-maximum_size:]

    @staticmethod
    def _select_join_separator(
        *,
        overlap_text: str,
        current_segment: str,
    ) -> str:
        """
        Choose a readable separator between overlap and current content.

        Paragraph-like content is separated using a blank line. Otherwise,
        one space is used.
        """

        if "\n" in overlap_text or "\n" in current_segment:
            return "\n\n"

        return " "
