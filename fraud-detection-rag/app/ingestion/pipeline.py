from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.ingestion.builders import ChunkBuilder
from app.ingestion.chunk_schema import Chunk
from app.ingestion.chunkers import BaseChunker
from app.ingestion.overlap import OverlapProcessor
from app.ingestion.processors import TextNormalizer
from app.ingestion.schemas import Document


class ChunkingPipelineError(RuntimeError):
    """
    Base exception raised when the chunking pipeline fails.

    Pipeline-specific exceptions make it easier for API handlers, background
    workers, and ingestion jobs to distinguish ingestion failures from
    unrelated application errors.
    """


class TextNormalizationError(ChunkingPipelineError):
    """
    Raised when document text normalization fails.
    """


class TextChunkingError(ChunkingPipelineError):
    """
    Raised when the configured chunking strategy fails.
    """


class OverlapProcessingError(ChunkingPipelineError):
    """
    Raised when overlap processing fails.
    """


class ChunkBuildingError(ChunkingPipelineError):
    """
    Raised when final Chunk object construction fails.
    """


class ChunkingPipeline:
    """
    Orchestrate the complete document chunking workflow.

    Processing flow:

        Document
            ↓
        TextNormalizer
            ↓
        BaseChunker implementation
            ↓
        OverlapProcessor
            ↓
        ChunkBuilder
            ↓
        list[Chunk]

    The pipeline coordinates components but does not implement their internal
    algorithms.

    This class is the public API for the chunking subsystem.
    """

    def __init__(
        self,
        *,
        chunker: BaseChunker,
        strategy_name: str,
        normalizer: TextNormalizer | None = None,
        overlap_processor: OverlapProcessor | None = None,
        builder: ChunkBuilder | None = None,
        pipeline_version: str = "1.0.0",
    ) -> None:
        """
        Initialize the chunking pipeline.

        Args:
            chunker:
                Concrete chunking strategy, such as ParagraphChunker or
                RecursiveChunker.

            strategy_name:
                Stable strategy identifier stored in chunk metadata.

                Examples:
                    - paragraph
                    - recursive
                    - semantic
                    - markdown

            normalizer:
                Optional text normalizer. A default TextNormalizer is created
                when one is not supplied.

            overlap_processor:
                Optional overlap processor. By default, one is created using
                the chunker's configuration.

            builder:
                Optional ChunkBuilder. A default instance is created when one
                is not supplied.

            pipeline_version:
                Version identifier written into generated chunk metadata.

        Raises:
            TypeError:
                When supplied dependencies have invalid types.

            ValueError:
                When strategy_name or pipeline_version is empty, or when the
                overlap processor uses a different configuration.
        """

        self._chunker = chunker
        self._strategy_name = self._normalize_required_name(
            value=strategy_name,
            field_name="strategy_name",
        )

        self._pipeline_version = self._normalize_required_name(
            value=pipeline_version,
            field_name="pipeline_version",
            lowercase=False,
        )

        self._normalizer = normalizer or TextNormalizer()
        self._overlap_processor = overlap_processor or OverlapProcessor(chunker.config)
        self._builder = builder or ChunkBuilder()

        self._validate_dependencies()

    @property
    def chunker(self) -> BaseChunker:
        """
        Return the configured chunking strategy.
        """

        return self._chunker

    @property
    def strategy_name(self) -> str:
        """
        Return the normalized chunking strategy name.
        """

        return self._strategy_name

    @property
    def pipeline_version(self) -> str:
        """
        Return the pipeline version stored in generated metadata.
        """

        return self._pipeline_version

    def process(
        self,
        document: Document,
        *,
        additional_metadata: Mapping[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Process one Document into retrieval-ready Chunk objects.

        Args:
            document:
                Validated source document.

            additional_metadata:
                Optional metadata applied to every generated chunk.

                Pipeline-protected metadata is written after this mapping and
                cannot be overridden by callers.

        Returns:
            Ordered validated Chunk objects.

        Raises:
            TypeError:
                When document is not a Document instance or
                additional_metadata is invalid.

            TextNormalizationError:
                When normalization fails.

            TextChunkingError:
                When the configured chunker fails.

            OverlapProcessingError:
                When overlap processing fails.

            ChunkBuildingError:
                When final Chunk creation fails.
        """

        supplied_metadata = self._prepare_additional_metadata(additional_metadata)

        normalized_text = self._normalize_document_text(document)

        if not normalized_text:
            return []

        original_segments = self._split_text(normalized_text)

        if not original_segments:
            return []

        processed_segments = self._apply_overlap(original_segments)

        if not processed_segments:
            return []

        pipeline_metadata = self._build_pipeline_metadata(
            document=document,
            normalized_text=normalized_text,
            original_segments=original_segments,
            processed_segments=processed_segments,
        )

        final_metadata = {
            **supplied_metadata,
            **pipeline_metadata,
        }

        return self._build_chunks(
            document=document,
            segments=processed_segments,
            metadata=final_metadata,
        )

    def _normalize_document_text(
        self,
        document: Document,
    ) -> str:
        """
        Normalize source document text.

        The original exception is preserved as the cause using `raise from`.
        This provides a readable pipeline error while retaining the complete
        traceback for debugging.
        """

        try:
            return self._normalizer.normalize(document.content)
        except Exception as exc:
            raise TextNormalizationError(
                f"Failed to normalize document text for source {document.source!r}."
            ) from exc

    def _split_text(
        self,
        normalized_text: str,
    ) -> list[str]:
        """
        Split normalized text using the configured chunking strategy.
        """

        try:
            return self._chunker.split(normalized_text)
        except Exception as exc:
            raise TextChunkingError(
                "Chunking strategy "
                f"{self.strategy_name!r} failed to split normalized text."
            ) from exc

    def _apply_overlap(
        self,
        segments: list[str],
    ) -> list[str]:
        """
        Apply contextual overlap to generated text segments.
        """

        try:
            return self._overlap_processor.apply(segments)
        except Exception as exc:
            raise OverlapProcessingError(
                f"Failed to apply overlap to {len(segments)} text segment(s)."
            ) from exc

    def _build_chunks(
        self,
        *,
        document: Document,
        segments: list[str],
        metadata: Mapping[str, Any],
    ) -> list[Chunk]:
        """
        Convert processed segments into validated Chunk objects.
        """

        try:
            return self._builder.build_many(
                document=document,
                segments=segments,
                strategy=self.strategy_name,
                additional_metadata=metadata,
            )
        except Exception as exc:
            raise ChunkBuildingError(
                f"Failed to build Chunk objects for source {document.source!r}."
            ) from exc

    def _build_pipeline_metadata(
        self,
        *,
        document: Document,
        normalized_text: str,
        original_segments: list[str],
        processed_segments: list[str],
    ) -> dict[str, Any]:
        """
        Build metadata describing how the document was processed.

        This metadata is useful for:

        - debugging
        - pipeline evaluation
        - vector-store filtering
        - version migrations
        - detecting stale chunks
        - comparing chunking configurations
        """

        config = self.chunker.config

        return {
            "pipeline_version": self.pipeline_version,
            "chunking_strategy": self.strategy_name,
            "target_chunk_size": config.target_size,
            "minimum_chunk_size": config.min_chunk_size,
            "requested_overlap": config.overlap,
            "overlap_enabled": config.overlap > 0,
            "preserve_headings": config.preserve_headings,
            "source_content_size": len(document.content),
            "normalized_content_size": len(normalized_text),
            "segments_before_overlap": len(original_segments),
            "segments_after_overlap": len(processed_segments),
        }

    def _validate_dependencies(self) -> None:
        """
        Validate injected pipeline dependencies.

        The overlap processor must use the same ChunkConfig as the chunker.
        Otherwise, the chunker and overlap stages could disagree about target
        size, overlap, whitespace handling, or empty-segment behaviour.
        """

        if not isinstance(self._normalizer, TextNormalizer):
            raise TypeError(
                "normalizer must be an instance of TextNormalizer, "
                f"received {type(self._normalizer).__name__}."
            )

        if not isinstance(self._overlap_processor, OverlapProcessor):
            raise TypeError(
                "overlap_processor must be an instance of OverlapProcessor, "
                f"received {type(self._overlap_processor).__name__}."
            )

        if not isinstance(self._builder, ChunkBuilder):
            raise TypeError(
                "builder must be an instance of ChunkBuilder, "
                f"received {type(self._builder).__name__}."
            )

        if self._overlap_processor.config != self.chunker.config:
            raise ValueError(
                "The chunker and overlap processor must use the same ChunkConfig."
            )

    @staticmethod
    def _prepare_additional_metadata(
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Validate and copy caller-provided metadata.

        A copy prevents the pipeline from mutating the caller's mapping.
        """

        if metadata is None:
            return {}

        return dict(metadata)

    @staticmethod
    def _normalize_required_name(
        *,
        value: str,
        field_name: str,
        lowercase: bool = True,
    ) -> str:
        """
        Validate and normalize required string identifiers.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized.lower() if lowercase else normalized
