from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Cricket Intelligence API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://cricket:cricket@localhost:5433/cricket_db"
    test_database_url: str = "postgresql+asyncpg://cricket:cricket@localhost:5433/cricket_test_db"
    log_level: str = "INFO"
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")
    jwt_secret_key: str = "replace-me-with-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    ai_enabled: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ai_request_timeout_seconds: int = 30
    ai_max_retries: int = 1

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
