from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from openai import OpenAI

from app.llm.base_llm import BaseLLM
from app.llm.llm_config import LLMConfig
from app.llm.llm_schema import (
    LLMRequest,
    LLMResponse,
    LLMStreamEvent,
)


class LLMGenerationError(RuntimeError):
    """
    Raised when the provider cannot generate a usable response.
    """


class OpenAILLM(BaseLLM):
    """
    OpenAI Responses API implementation.

    Supports both:

    - normal complete responses
    - streamed text-delta responses
    """

    PROVIDER_NAME = "openai"

    def __init__(
        self,
        config: LLMConfig,
    ) -> None:
        super().__init__(config)

        client_arguments: dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.timeout_seconds,
            "max_retries": config.max_retries,
        }

        if config.base_url is not None:
            client_arguments["base_url"] = (
                config.base_url
            )

        self._client = OpenAI(
            **client_arguments
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate one complete answer.
        """

        self._validate_request(request)

        try:
            response = self._client.responses.create(
                model=self.config.model_name,
                instructions=request.instructions,
                input=request.user_input,
                max_output_tokens=(
                    self.config.max_output_tokens
                ),
            )
        except Exception as exc:
            raise LLMGenerationError(
                "The LLM provider failed to generate "
                "a response."
            ) from exc

        response_text = self._extract_response_text(
            response
        )

        if not response_text:
            raise LLMGenerationError(
                "The LLM provider returned an empty response."
            )

        usage = getattr(
            response,
            "usage",
            None,
        )

        response_id = getattr(
            response,
            "id",
            None,
        )

        return LLMResponse(
            text=response_text,
            model_name=self.config.model_name,
            provider=self.PROVIDER_NAME,
            response_id=(
                str(response_id)
                if response_id is not None
                else None
            ),
            input_tokens=self._read_usage_value(
                usage,
                "input_tokens",
            ),
            output_tokens=self._read_usage_value(
                usage,
                "output_tokens",
            ),
            total_tokens=self._read_usage_value(
                usage,
                "total_tokens",
            ),
        )

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[LLMStreamEvent]:
        """
        Stream generated text as provider-independent events.

        OpenAI emits many event types. This method exposes only:

        - response.output_text.delta
        - response.completed

        Provider-specific events remain hidden from the rest of the app.
        """

        self._validate_request(request)

        try:
            stream = self._client.responses.create(
                model=self.config.model_name,
                instructions=request.instructions,
                input=request.user_input,
                max_output_tokens=(
                    self.config.max_output_tokens
                ),
                stream=True,
            )

            completed_event_sent = False

            for event in stream:
                event_type = getattr(
                    event,
                    "type",
                    "",
                )

                if (
                    event_type
                    == "response.output_text.delta"
                ):
                    delta = getattr(
                        event,
                        "delta",
                        "",
                    )

                    if isinstance(delta, str) and delta:
                        yield LLMStreamEvent(
                            type="text_delta",
                            delta=delta,
                        )

                elif event_type == "response.completed":
                    response = getattr(
                        event,
                        "response",
                        None,
                    )

                    yield self._build_completed_event(
                        response
                    )

                    completed_event_sent = True

            if not completed_event_sent:
                yield LLMStreamEvent(
                    type="completed",
                    model_name=self.config.model_name,
                    provider=self.PROVIDER_NAME,
                )

        except Exception as exc:
            raise LLMGenerationError(
                "The LLM provider stream failed."
            ) from exc

    def _build_completed_event(
        self,
        response: Any,
    ) -> LLMStreamEvent:
        """
        Convert the provider completion event into our schema.
        """

        if response is None:
            return LLMStreamEvent(
                type="completed",
                model_name=self.config.model_name,
                provider=self.PROVIDER_NAME,
            )

        usage = getattr(
            response,
            "usage",
            None,
        )

        response_id = getattr(
            response,
            "id",
            None,
        )

        return LLMStreamEvent(
            type="completed",
            response_id=(
                str(response_id)
                if response_id is not None
                else None
            ),
            model_name=self.config.model_name,
            provider=self.PROVIDER_NAME,
            input_tokens=self._read_usage_value(
                usage,
                "input_tokens",
            ),
            output_tokens=self._read_usage_value(
                usage,
                "output_tokens",
            ),
            total_tokens=self._read_usage_value(
                usage,
                "total_tokens",
            ),
        )

    @staticmethod
    def _validate_request(
        request: LLMRequest,
    ) -> None:
        """
        Validate the request type.
        """

        if not isinstance(request, LLMRequest):
            raise TypeError(
                "OpenAILLM expected an LLMRequest, "
                f"received {type(request).__name__}."
            )

    @staticmethod
    def _extract_response_text(
        response: Any,
    ) -> str:
        """
        Extract complete output text.
        """

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if not isinstance(output_text, str):
            return ""

        return output_text.strip()

    @staticmethod
    def _read_usage_value(
        usage: Any,
        field_name: str,
    ) -> int | None:
        """
        Read an optional token-usage value.
        """

        if usage is None:
            return None

        value = getattr(
            usage,
            field_name,
            None,
        )

        return value if isinstance(value, int) else None