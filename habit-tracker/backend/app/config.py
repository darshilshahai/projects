from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to backend/ so it works no matter the cwd
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, value: str) -> str:
        url = (value or "").strip().rstrip("/")
        if not url:
            raise ValueError(
                "SUPABASE_URL is empty. Set it to https://YOUR_PROJECT_REF.supabase.co "
                "(Project Settings → API → Project URL). Do NOT use the postgres:// connection string."
            )
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            raise ValueError(
                "SUPABASE_URL must be the HTTP API URL (https://xxxx.supabase.co), "
                "not the database connection string (postgresql://...)."
            )
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(
                "SUPABASE_URL must start with https:// (e.g. https://xxxx.supabase.co)"
            )
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
