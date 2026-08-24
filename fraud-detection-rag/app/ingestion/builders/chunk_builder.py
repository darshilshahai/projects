from __future__ import annotations
import hashlib
from collections.abc import Mapping, Sequence
from typing import Any
from app.ingestion.chunk_schema import Chunk
from app.ingestion.schemas import Document


class ChunkBuilder:
    """
    Convert processed text segments into validated Chunk objects.

    The builder is responsible for:

    - validating incoming text segments
    - generating deterministic chunk IDs
    - assigning zero-based chunk indexes
    - propagating document metadata
    - adding chunk-level metadata
    - creating validated Chunk models

    The builder is not responsible for:

    - loading documents
    - normalizing text
    - splitting text
    - applying overlap
    - generating embeddings
    - storing chunks in a vector database
    """

    HASH_ALGORITHM = "sha256"
    ID_NAMESPACE = "rag-chunk-v1"

    def build_many(
        self,
        *,
        document: Document,
        segments: Sequence[str],
        strategy: str,
        additional_metadata: Mapping[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Build an ordered collection of Chunk objects.

        Args:
            document:
                Source document from which the segments were produced.

            segments:
                Ordered processed text segments. These may already contain
                overlap.

            strategy:
                Name of the chunking strategy used, such as:
                    - paragraph
                    - recursive
                    - semantic
                    - markdown

            additional_metadata:
                Optional metadata applied to every generated chunk.

        Returns:
            Ordered validated Chunk objects.

        Raises:
            TypeError:
                When segments is not a sequence of strings, when strategy is
                not a string, or when additional_metadata is not a mapping.

            ValueError:
                When strategy is empty or no valid segments remain.
        """

        normalized_strategy = self._validate_strategy(strategy)
        prepared_segments = self._prepare_segments(segments)
        shared_metadata = self._prepare_additional_metadata(additional_metadata)

        if not prepared_segments:
            return []

        total_chunks = len(prepared_segments)
        chunks: list[Chunk] = []

        for chunk_index, content in enumerate(prepared_segments):
            chunk = self.build_one(
                document=document,
                content=content,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                strategy=normalized_strategy,
                additional_metadata=shared_metadata,
            )

            chunks.append(chunk)

        return chunks

    def build_one(
        self,
        *,
        document: Document,
        content: str,
        chunk_index: int,
        total_chunks: int,
        strategy: str,
        additional_metadata: Mapping[str, Any] | None = None,
    ) -> Chunk:
        """
        Build one validated Chunk object.

        This method is public because some future pipeline stages may need to
        construct or rebuild an individual chunk without processing an entire
        collection.

        Args:
            document:
                Original source document.

            content:
                Final text assigned to this chunk.

            chunk_index:
                Zero-based position of the chunk within the document.

            total_chunks:
                Total number of chunks generated from the document.

            strategy:
                Name of the chunking strategy used.

            additional_metadata:
                Optional metadata applied to this chunk.

        Returns:
            A validated Chunk object.
        """

        prepared_content = self._validate_content(content)
        normalized_strategy = self._validate_strategy(strategy)

        self._validate_chunk_index(
            chunk_index=chunk_index,
            total_chunks=total_chunks,
        )

        shared_metadata = self._prepare_additional_metadata(additional_metadata)

        chunk_id = self._generate_chunk_id(
            source=document.source,
            content=prepared_content,
            chunk_index=chunk_index,
            strategy=normalized_strategy,
        )

        metadata = self._build_metadata(
            document=document,
            content=prepared_content,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            strategy=normalized_strategy,
            additional_metadata=shared_metadata,
        )

        return Chunk(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            content=prepared_content,
            source=document.source,
            metadata=metadata,
        )

    def _prepare_segments(
        self,
        segments: Sequence[str],
    ) -> list[str]:
        """
        Validate and prepare the incoming segment collection.

        Empty and whitespace-only values are removed because they must never
        reach embedding or storage layers.
        """

        if isinstance(segments, str):
            raise TypeError(
                "ChunkBuilder expected a sequence of strings, "
                "but received a single string."
            )

        prepared_segments: list[str] = []

        for index, segment in enumerate(segments):
            if not isinstance(segment, str):
                raise TypeError(
                    "ChunkBuilder expected every segment to be a string, "
                    f"but item {index} is {type(segment).__name__}."
                )

            prepared = segment.strip()

            if not prepared:
                continue

            prepared_segments.append(prepared)

        return prepared_segments

    @staticmethod
    def _validate_content(content: str) -> str:
        """
        Validate and normalize individual chunk content.
        """

        prepared = content.strip()

        if not prepared:
            raise ValueError("Chunk content cannot be empty or whitespace-only.")

        return prepared

    @staticmethod
    def _validate_strategy(strategy: str) -> str:
        """
        Validate and normalize the chunking strategy name.

        Strategy names are normalized to lowercase so metadata remains
        consistent across the codebase.
        """

        normalized = strategy.strip().lower()

        if not normalized:
            raise ValueError("Chunking strategy cannot be empty.")

        return normalized

    @staticmethod
    def _validate_chunk_index(
        *,
        chunk_index: int,
        total_chunks: int,
    ) -> None:
        """
        Validate chunk ordering values.
        """

        if chunk_index < 0:
            raise ValueError("chunk_index cannot be negative.")

        if total_chunks <= 0:
            raise ValueError("total_chunks must be greater than zero.")

        if chunk_index >= total_chunks:
            raise ValueError("chunk_index must be smaller than total_chunks.")

    @staticmethod
    def _prepare_additional_metadata(
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Copy optional shared metadata into a regular dictionary.

        Returning a new dictionary prevents callers from later mutating the
        metadata object stored inside generated chunks.
        """

        if metadata is None:
            return {}

        return dict(metadata)

    def _build_metadata(
        self,
        *,
        document: Document,
        content: str,
        chunk_index: int,
        total_chunks: int,
        strategy: str,
        additional_metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Build final metadata for one chunk.

        Metadata precedence is:

            document metadata
                ↓
            additional pipeline metadata
                ↓
            protected chunk metadata

        Protected chunk fields are written last so callers cannot accidentally
        override values such as chunk_index or chunk_size.
        """

        metadata: dict[str, Any] = {
            **document.metadata,
            **additional_metadata,
            "file_type": document.file_type,
            "chunk_index": chunk_index,
            "chunk_number": chunk_index + 1,
            "total_chunks": total_chunks,
            "chunk_size": len(content),
            "chunking_strategy": strategy,
            "is_first_chunk": chunk_index == 0,
            "is_last_chunk": chunk_index == total_chunks - 1,
        }

        return {key: value for key, value in metadata.items() if value is not None}

    def _generate_chunk_id(
        self,
        *,
        source: str,
        content: str,
        chunk_index: int,
        strategy: str,
    ) -> str:
        """
        Generate a deterministic SHA-256 chunk identifier.

        The identifier is derived from:

        - ID namespace/version
        - source identifier
        - chunking strategy
        - chunk index
        - final chunk content

        Identical inputs produce identical IDs.

        Any meaningful change to the source, strategy, ordering, or content
        produces a different ID.
        """

        canonical_value = "\x1f".join(
            (
                self.ID_NAMESPACE,
                source,
                strategy,
                str(chunk_index),
                content,
            )
        )

        digest = hashlib.new(self.HASH_ALGORITHM)
        digest.update(canonical_value.encode("utf-8"))

        return digest.hexdigest()
