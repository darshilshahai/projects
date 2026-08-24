from __future__ import annotations
from collections.abc import Sequence
from app.ingestion.chunkers.base_chunker import BaseChunker


class RecursiveChunker(BaseChunker):
    """
    Split text recursively using progressively weaker semantic boundaries.

    The separator order is provided by ChunkConfig. The default hierarchy is:

        1. Double newline: paragraph boundary
        2. Single newline: line boundary
        3. ". ": lightweight sentence boundary
        4. Space: word boundary
        5. Empty string: character-level fallback

    The chunker attempts to preserve the strongest available semantic
    boundary. It only moves to a weaker separator when the current piece
    remains larger than target_size.

    The class returns plain strings. It does not create Chunk objects,
    generate IDs, apply overlap, or manage metadata.
    """

    def split(self, text: str) -> list[str]:
        """
        Split normalized text into retrieval-oriented segments.

        Processing steps:

        1. Validate and prepare the input.
        2. Recursively split oversized text.
        3. Greedily merge compatible pieces.
        4. Merge a small final remainder where possible.
        5. Apply shared cleanup from BaseChunker.

        Args:
            text:
                Normalized source text.

        Returns:
            Ordered text segments.

        Raises:
            TypeError:
                When text is not a string.
        """

        prepared_text = self._prepare_text(text)

        if not prepared_text:
            return []

        segments = self._recursive_split(
            text=prepared_text,
            separators=self.config.separators,
        )

        segments = self._merge_small_final_segment(segments)

        return self._finalize_segments(segments)

    def _recursive_split(
        self,
        *,
        text: str,
        separators: Sequence[str],
    ) -> list[str]:
        """
        Recursively split text using the supplied separator hierarchy.

        Base cases:

        - Text already fits target_size.
        - No separators remain.
        - The active separator is the character fallback.

        Args:
            text:
                Current text fragment being processed.

            separators:
                Remaining separators ordered from strongest to weakest.

        Returns:
            Text fragments that do not exceed target_size.
        """

        prepared_text = text.strip() if self.config.strip_chunks else text

        if not prepared_text:
            return []

        if len(prepared_text) <= self.config.target_size:
            return [prepared_text]

        if not separators:
            return self._split_by_characters(prepared_text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            return self._split_by_characters(prepared_text)

        if separator not in prepared_text:
            return self._recursive_split(
                text=prepared_text,
                separators=remaining_separators,
            )

        pieces = self._split_preserving_separator(
            text=prepared_text,
            separator=separator,
        )

        if len(pieces) <= 1:
            return self._recursive_split(
                text=prepared_text,
                separators=remaining_separators,
            )

        return self._merge_and_recursively_split(
            pieces=pieces,
            separator=separator,
            remaining_separators=remaining_separators,
        )

    def _merge_and_recursively_split(
        self,
        *,
        pieces: list[str],
        separator: str,
        remaining_separators: Sequence[str],
    ) -> list[str]:
        """
        Greedily merge split pieces while respecting target_size.

        When an individual piece still exceeds target_size, it is recursively
        processed with weaker separators.

        Example:

            Text split by paragraphs:
                paragraph A: 300 characters
                paragraph B: 400 characters
                paragraph C: 1,800 characters

            target_size:
                1,000 characters

            Behaviour:
                A and B may be merged.
                C is recursively split using line, sentence, word, or
                character boundaries.
        """

        segments: list[str] = []
        current_pieces: list[str] = []
        current_size = 0

        for piece in pieces:
            prepared_piece = piece.strip() if self.config.strip_chunks else piece

            if not prepared_piece:
                continue

            piece_size = len(prepared_piece)

            if piece_size > self.config.target_size:
                if current_pieces:
                    segments.append(
                        self._join_pieces(
                            current_pieces,
                            separator,
                        )
                    )
                    current_pieces = []
                    current_size = 0

                recursively_split = self._recursive_split(
                    text=prepared_piece,
                    separators=remaining_separators,
                )

                segments.extend(recursively_split)
                continue

            separator_size = len(separator) if current_pieces else 0
            candidate_size = current_size + separator_size + piece_size

            if candidate_size <= self.config.target_size:
                current_pieces.append(prepared_piece)
                current_size = candidate_size
                continue

            if current_pieces:
                segments.append(
                    self._join_pieces(
                        current_pieces,
                        separator,
                    )
                )

            current_pieces = [prepared_piece]
            current_size = piece_size

        if current_pieces:
            segments.append(
                self._join_pieces(
                    current_pieces,
                    separator,
                )
            )

        return segments

    def _split_preserving_separator(
        self,
        *,
        text: str,
        separator: str,
    ) -> list[str]:
        """
        Split text without permanently losing its separator semantics.

        Python's str.split() removes separators. That is acceptable only when
        the same separator is restored during merging.

        This method deliberately returns clean logical pieces. The active
        separator is later reinserted by _join_pieces() when adjacent pieces
        are packed into the same output segment.

        Args:
            text:
                Text to split.

            separator:
                Active separator.

        Returns:
            Non-empty logical pieces.
        """

        raw_pieces = text.split(separator)

        pieces: list[str] = []

        for piece in raw_pieces:
            prepared_piece = piece.strip() if self.config.strip_chunks else piece

            if self.config.drop_empty_chunks and not prepared_piece.strip():
                continue

            pieces.append(prepared_piece)

        return pieces

    def _split_by_characters(
        self,
        text: str,
    ) -> list[str]:
        """
        Split text into fixed-size character windows.

        This is the final fallback and guarantees that no segment exceeds
        target_size.

        Character splitting may break words or structured identifiers, so it
        is used only when all stronger separators have failed.
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
        Merge an undersized final segment with its predecessor when possible.

        The merge occurs only when:

        - At least two segments exist.
        - The final segment is smaller than min_chunk_size.
        - The combined size does not exceed target_size.

        The separator between final chunks is chosen conservatively as a
        paragraph boundary because the original recursive separator may differ
        between segments.
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
    def _join_pieces(
        pieces: list[str],
        separator: str,
    ) -> str:
        """
        Rejoin pieces using the active semantic separator.
        """

        return separator.join(pieces)
