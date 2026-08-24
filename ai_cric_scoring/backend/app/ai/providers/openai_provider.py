from __future__ import annotations

import time
from typing import TypeVar

from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.ai.schemas.provider import StructuredGeneration
from app.core.config import Settings
from app.core.exceptions import AIInvalidResponseError, AIProviderError, AITimeoutError

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key or None,
            timeout=float(settings.ai_request_timeout_seconds),
            max_retries=0,
        )

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> StructuredGeneration[T]:
        if not self._settings.openai_api_key:
            raise AIProviderError("OpenAI API key is not configured.")
        started = time.perf_counter()
        try:
            completion = await self._client.chat.completions.parse(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_model,
            )
        except APITimeoutError as exc:
            raise AITimeoutError() from exc
        except OpenAIError as exc:
            raise AIProviderError("Unable to generate analysis right now.") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        message = completion.choices[0].message
        if message.parsed is None:
            raise AIInvalidResponseError("Provider returned an unparsable structured response.")
        usage = completion.usage
        return StructuredGeneration(
            data=message.parsed,
            provider="openai",
            model=completion.model or self._settings.openai_model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            latency_ms=latency_ms,
        )
