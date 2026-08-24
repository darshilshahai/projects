from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QueryMint"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_reload: bool = True

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-terra"

    dataset_storage_path: Path = Path("storage/datasets")

    max_upload_size_mb: int = Field(
        default=25,
        ge=1,
        le=500,
    )

    csv_sample_rows: int = Field(
        default=5,
        ge=1,
        le=50,
    )

    csv_preview_rows: int = Field(
        default=20,
        ge=1,
        le=200,
    )

    max_query_rows: int = Field(
        default=200,
        ge=1,
        le=5000,
    )

    max_tool_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    openai_input_price_per_million: float = Field(
        default=2.50,
        ge=0,
    )

    openai_cached_input_price_per_million: float = Field(
        default=0.25,
        ge=0,
    )

    openai_output_price_per_million: float = Field(
        default=15.00,
        ge=0,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    settings.dataset_storage_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return settings