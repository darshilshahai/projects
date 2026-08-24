from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from app.embeddings.base_embedder import BaseEmbedder
from app.embeddings.embedding_config import EmbeddingConfig
from app.embeddings.embedding_schema import EmbeddingBatch


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Local embedding implementation using Sentence Transformers.

    The model is loaded once during object construction and reused for every
    embedding request.
    """

    def __init__(
        self,
        config: EmbeddingConfig,
    ) -> None:
        super().__init__(config)

        model_arguments: dict[str, Any] = {}

        if config.device is not None:
            model_arguments["device"] = config.device

        self._model = SentenceTransformer(
            config.model_name,
            **model_arguments,
        )

        model_dimension = self._model.get_sentence_embedding_dimension()

        if model_dimension is None or model_dimension <= 0:
            raise ValueError(
                "Could not determine the embedding dimension for model "
                f"{config.model_name!r}."
            )

        self._dimension = int(model_dimension)

    @property
    def dimension(self) -> int:
        """
        Return the vector size produced by the loaded model.
        """

        return self._dimension

    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        ids: Sequence[str] | None = None,
        metadata: Sequence[Mapping[str, Any]] | None = None,
    ) -> EmbeddingBatch:
        """
        Convert multiple texts into normalized or unnormalized vectors.

        Args:
            texts:
                Ordered source texts.

            ids:
                Optional ordered identifiers. When omitted, deterministic
                positional identifiers are generated.

            metadata:
                Optional metadata entry for every input text.

        Returns:
            Validated EmbeddingBatch.
        """

        prepared_texts = self._prepare_texts(texts)
        prepared_ids = self._prepare_ids(
            ids=ids,
            total_texts=len(prepared_texts),
        )
        prepared_metadata = self._prepare_metadata(
            metadata=metadata,
            total_texts=len(prepared_texts),
        )

        if not prepared_texts:
            return EmbeddingBatch(
                ids=(),
                texts=(),
                vectors=(),
                model_name=self.config.model_name,
                dimension=self.dimension,
                normalized=self.config.normalize_embeddings,
                metadata=(),
            )

        encoded = self._model.encode(
            prepared_texts,
            batch_size=self.config.batch_size,
            show_progress_bar=self.config.show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=self.config.normalize_embeddings,
        )

        vectors = self._convert_vectors(encoded)

        return EmbeddingBatch(
            ids=tuple(prepared_ids),
            texts=tuple(prepared_texts),
            vectors=vectors,
            model_name=self.config.model_name,
            dimension=self.dimension,
            normalized=self.config.normalize_embeddings,
            metadata=tuple(prepared_metadata),
        )

    @staticmethod
    def _prepare_texts(
        texts: Sequence[str],
    ) -> list[str]:
        """
        Validate and clean input text.

        Empty texts are rejected rather than silently removed because removing
        one item would break positional alignment with IDs and metadata.
        """

        if isinstance(texts, (str, bytes)):
            raise TypeError(
                "embed_texts expected a sequence of strings, "
                "but received a single string."
            )

        prepared_texts: list[str] = []

        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise TypeError(
                    "Every embedding input must be a string, "
                    f"but item {index} is {type(text).__name__}."
                )

            prepared = text.strip()

            if not prepared:
                raise ValueError(f"Embedding text at index {index} cannot be empty.")

            prepared_texts.append(prepared)

        return prepared_texts

    @staticmethod
    def _prepare_ids(
        *,
        ids: Sequence[str] | None,
        total_texts: int,
    ) -> list[str]:
        """
        Validate supplied IDs or generate positional IDs.
        """

        if ids is None:
            return [f"text-{index}" for index in range(total_texts)]

        if isinstance(ids, (str, bytes)):
            raise TypeError("Embedding IDs must be a sequence of strings.")

        if len(ids) != total_texts:
            raise ValueError(
                "The number of embedding IDs must match the number of texts."
            )

        prepared_ids: list[str] = []

        for index, identifier in enumerate(ids):
            if not isinstance(identifier, str):
                raise TypeError(
                    "Every embedding ID must be a string, "
                    f"but item {index} is {type(identifier).__name__}."
                )

            prepared = identifier.strip()

            if not prepared:
                raise ValueError(f"Embedding ID at index {index} cannot be empty.")

            prepared_ids.append(prepared)

        return prepared_ids

    @staticmethod
    def _prepare_metadata(
        *,
        metadata: Sequence[Mapping[str, Any]] | None,
        total_texts: int,
    ) -> list[dict[str, Any]]:
        """
        Validate metadata and copy every mapping.
        """

        if metadata is None:
            return [{} for _ in range(total_texts)]

        if isinstance(metadata, (str, bytes)):
            raise TypeError("Embedding metadata must be a sequence of mappings.")

        if len(metadata) != total_texts:
            raise ValueError(
                "The number of metadata entries must match the number of texts."
            )

        prepared_metadata: list[dict[str, Any]] = []

        for index, item in enumerate(metadata):
            if not isinstance(item, Mapping):
                raise TypeError(
                    "Every embedding metadata entry must be a mapping, "
                    f"but item {index} is {type(item).__name__}."
                )

            prepared_metadata.append(dict(item))

        return prepared_metadata

    def _convert_vectors(
        self,
        encoded: np.ndarray,
    ) -> tuple[tuple[float, ...], ...]:
        """
        Convert NumPy output into immutable Python vectors.

        The dimension of every vector is checked before returning.
        """

        if encoded.ndim == 1:
            encoded = encoded.reshape(1, -1)

        if encoded.ndim != 2:
            raise ValueError(
                f"Embedding model returned an unexpected array shape: {encoded.shape}."
            )

        if encoded.shape[1] != self.dimension:
            raise ValueError(
                "Embedding model returned vectors with dimension "
                f"{encoded.shape[1]}, but expected {self.dimension}."
            )

        return tuple(tuple(float(value) for value in vector) for vector in encoded)
