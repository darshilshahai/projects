from dataclasses import dataclass
from typing import Any


@dataclass
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0

    def add_response(self, response: Any) -> None:
        usage = getattr(
            response,
            "usage",
            None,
        )

        if usage is None:
            return

        self.llm_calls += 1

        input_tokens = int(
            getattr(
                usage,
                "input_tokens",
                0,
            )
            or 0
        )

        output_tokens = int(
            getattr(
                usage,
                "output_tokens",
                0,
            )
            or 0
        )

        total_tokens = int(
            getattr(
                usage,
                "total_tokens",
                input_tokens + output_tokens,
            )
            or 0
        )

        input_details = getattr(
            usage,
            "input_tokens_details",
            None,
        )

        output_details = getattr(
            usage,
            "output_tokens_details",
            None,
        )

        cached_tokens = 0
        reasoning_tokens = 0

        if input_details is not None:
            cached_tokens = int(
                getattr(
                    input_details,
                    "cached_tokens",
                    0,
                )
                or 0
            )

        if output_details is not None:
            reasoning_tokens = int(
                getattr(
                    output_details,
                    "reasoning_tokens",
                    0,
                )
                or 0
            )

        self.input_tokens += input_tokens
        self.cached_input_tokens += cached_tokens
        self.output_tokens += output_tokens
        self.reasoning_tokens += reasoning_tokens
        self.total_tokens += total_tokens
