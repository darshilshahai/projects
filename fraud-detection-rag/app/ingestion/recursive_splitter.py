from __future__ import annotations
from typing import List
from app.ingestion.chunk_config import ChunkConfig


class RecursiveSplitter:
    """
    Responsible only for recursively splitting text.

    It knows nothing about:
    - Document
    - Chunk
    - Metadata
    - IDs
    """

    def __init__(self, config: ChunkConfig):
        self.config = config

    def split(self, text: str) -> List[str]:
        """
        Public entry point.
        """
        return self._recursive_split(text.strip(), list(self.config.separators))

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.config.target_size:
            return [text]

        if not separators:
            return self._character_split(text)

        separator = separators[0]
        remaining = separators[1:]

        if separator == "":
            return self._character_split(text)

        pieces = text.split(separator)

        if len(pieces) == 1:
            return self._recursive_split(
                text,
                remaining,
            )

        results: List[str] = []

        current = ""

        for piece in pieces:
            candidate = piece if not current else current + separator + piece

            if len(candidate) <= self.config.target_size:
                current = candidate

            else:
                if current:
                    results.extend(
                        self._recursive_split(
                            current,
                            remaining,
                        )
                    )

                current = piece

        if current:
            results.extend(
                self._recursive_split(
                    current,
                    remaining,
                )
            )

        return results

    def _character_split(
        self,
        text: str,
    ) -> List[str]:

        return [
            text[i : i + self.config.target_size]
            for i in range(
                0,
                len(text),
                self.config.target_size,
            )
        ]
