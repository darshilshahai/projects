from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """
    Input sent to the language model.
    """

    instructions: str
    user_input: str

    def __post_init__(self) -> None:
        if not isinstance(self.instructions, str):
            raise TypeError(
                "LLM instructions must be a string."
            )

        if not self.instructions.strip():
            raise ValueError(
                "LLM instructions cannot be empty."
            )

        if not isinstance(self.user_input, str):
            raise TypeError(
                "LLM user input must be a string."
            )

        if not self.user_input.strip():
            raise ValueError(
                "LLM user input cannot be empty."
            )


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """
    Complete normalized response returned by an LLM provider.
    """

    text: str
    model_name: str
    provider: str
    response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(
                "LLM response text must be a string."
            )

        if not self.text.strip():
            raise ValueError(
                "LLM response text cannot be empty."
            )

        if not isinstance(self.model_name, str):
            raise TypeError(
                "LLM model name must be a string."
            )

        if not self.model_name.strip():
            raise ValueError(
                "LLM model name cannot be empty."
            )

        if not isinstance(self.provider, str):
            raise TypeError(
                "LLM provider must be a string."
            )

        if not self.provider.strip():
            raise ValueError(
                "LLM provider cannot be empty."
            )


LLMStreamEventType = Literal[
    "text_delta",
    "completed",
]


@dataclass(frozen=True, slots=True)
class LLMStreamEvent:
    """
    One provider-independent event emitted during LLM streaming.

    text_delta:
        Contains newly generated text.

    completed:
        Signals that generation finished and includes final provider
        metadata and token usage.
    """

    type: LLMStreamEventType
    delta: str = ""
    response_id: str | None = None
    model_name: str | None = None
    provider: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.type == "text_delta":
            if not isinstance(self.delta, str):
                raise TypeError(
                    "Stream delta must be a string."
                )

            if not self.delta:
                raise ValueError(
                    "Text-delta events must contain text."
                )