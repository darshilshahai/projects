from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers.base import AIProvider
from app.ai.schemas.provider import StructuredGeneration
from app.core.config import Settings
from app.core.exceptions import AIDisabledError

T = TypeVar("T", bound=BaseModel)


class AIService:
    def __init__(self, provider: AIProvider, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> StructuredGeneration[T]:
        if not self._settings.ai_enabled:
            raise AIDisabledError()
        return await self._provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
        )
