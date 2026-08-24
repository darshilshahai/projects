import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


class Settings:
    openai_api_key: str
    research_model: str
    analysis_model: str
    app_env: str
    rate_limit_per_minute: int

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        research_model = os.getenv("RESEARCH_MODEL", "").strip()
        if not research_model:
            raise RuntimeError("RESEARCH_MODEL is not set")

        analysis_model = os.getenv("ANALYSIS_MODEL", "").strip()
        if not analysis_model:
            raise RuntimeError("ANALYSIS_MODEL is not set")

        self.openai_api_key = api_key
        self.research_model = research_model
        self.analysis_model = analysis_model
        self.app_env = os.getenv("APP_ENV", "development").strip().lower()
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key)
