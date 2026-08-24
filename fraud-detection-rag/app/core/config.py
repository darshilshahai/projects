from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.vectorstores.vector_store_config import DistanceMetric


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables and the local .env file.

    Environment variables are used so secrets and environment-specific
    settings are not hard-coded inside the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------

    app_name: str = Field(
        default="Healthcare Fraud RAG API",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="1.0.0",
        alias="APP_VERSION",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG",
    )

    api_v1_prefix: str = Field(
        default="/api/v1",
        alias="API_V1_PREFIX",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # ---------------------------------------------------------
    # Chunking
    # ---------------------------------------------------------

    chunk_target_size: int = Field(
        default=1_000,
        ge=100,
        alias="CHUNK_TARGET_SIZE",
    )

    chunk_overlap: int = Field(
        default=150,
        ge=0,
        alias="CHUNK_OVERLAP",
    )

    chunk_minimum_size: int = Field(
        default=100,
        ge=1,
        alias="CHUNK_MINIMUM_SIZE",
    )

    # ---------------------------------------------------------
    # Embeddings
    # ---------------------------------------------------------

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )

    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        alias="EMBEDDING_BATCH_SIZE",
    )

    embedding_device: str | None = Field(
        default=None,
        alias="EMBEDDING_DEVICE",
    )

    normalize_embeddings: bool = Field(
        default=True,
        alias="NORMALIZE_EMBEDDINGS",
    )

    # ---------------------------------------------------------
    # ChromaDB
    # ---------------------------------------------------------

    chroma_persist_directory: Path = Field(
        default=Path("data/chroma"),
        alias="CHROMA_PERSIST_DIRECTORY",
    )

    chroma_collection_name: str = Field(
        default="insurance_fraud_documents",
        alias="CHROMA_COLLECTION_NAME",
    )

    chroma_distance_metric: DistanceMetric = Field(
        default="cosine",
        alias="CHROMA_DISTANCE_METRIC",
    )

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    retrieval_top_k: int = Field(
        default=5,
        ge=1,
        alias="RETRIEVAL_TOP_K",
    )

    retrieval_fetch_k: int = Field(
        default=10,
        ge=1,
        alias="RETRIEVAL_FETCH_K",
    )

    retrieval_minimum_score: float | None = Field(
        default=None,
        alias="RETRIEVAL_MINIMUM_SCORE",
    )

    retrieval_maximum_context_characters: int = Field(
        default=8_000,
        ge=1,
        alias="RETRIEVAL_MAXIMUM_CONTEXT_CHARACTERS",
    )

    retrieval_near_duplicate_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        alias="RETRIEVAL_NEAR_DUPLICATE_THRESHOLD",
    )

    # ---------------------------------------------------------
    # LLM
    # ---------------------------------------------------------

    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        repr=False,
    )

    openai_model: str = Field(
        default="",
        alias="OPENAI_MODEL",
    )

    openai_base_url: str | None = Field(
        default=None,
        alias="OPENAI_BASE_URL",
    )

    llm_max_output_tokens: int = Field(
        default=1_000,
        ge=1,
        alias="LLM_MAX_OUTPUT_TOKENS",
    )

    llm_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        alias="LLM_TIMEOUT_SECONDS",
    )

    llm_max_retries: int = Field(
        default=2,
        ge=0,
        alias="LLM_MAX_RETRIES",
    )

    @field_validator("retrieval_minimum_score", mode="before")
    @classmethod
    def empty_minimum_score_to_none(cls, value: object) -> object:
        if value is None:
            return None

        if isinstance(value, str) and not value.strip():
            return None

        return value

    @field_validator(
        "app_name",
        "app_version",
        "environment",
        "api_v1_prefix",
        "embedding_model_name",
        "chroma_collection_name",
        "openai_api_key",
        "openai_model",
    )
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        """
        Remove extra surrounding whitespace and reject empty values.
        """

        normalized = value.strip()

        if not normalized:
            raise ValueError("Required application setting cannot be empty.")

        return normalized

    @field_validator("api_v1_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        """
        Ensure the API prefix begins with a slash.

        Example:

            api/v1  -> /api/v1
            /api/v1 -> /api/v1
        """

        normalized = value.strip().rstrip("/")

        if not normalized.startswith("/"):
            normalized = f"/{normalized}"

        return normalized

    @field_validator("embedding_device")
    @classmethod
    def normalize_embedding_device(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().lower()

        return normalized or None

    @field_validator("openai_base_url")
    @classmethod
    def normalize_base_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().rstrip("/")

        return normalized or None


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache one Settings instance.

    The first call reads environment variables and .env.

    Later calls return the same object.
    """

    return Settings()
