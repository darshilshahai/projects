from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.ai.schemas.provider import StructuredGeneration

T = TypeVar("T", bound=BaseModel)


class AIProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> StructuredGeneration[T]: ...
