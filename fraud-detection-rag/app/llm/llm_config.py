from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class LLMConfig(BaseModel):
    """
    Configuration used by an LLM implementation.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    model_name: str = Field(
        ...,
        min_length=1,
        description="Model used to generate answers.",
    )

    api_key: str = Field(
        ...,
        min_length=1,
        repr=False,
        description="Provider API key.",
    )

    base_url: str | None = Field(
        default=None,
        description="Optional OpenAI-compatible base URL.",
    )

    max_output_tokens: int = Field(
        default=300,
        ge=1,
        le=32_000,
        description=(
            "Maximum answer length. A smaller value prevents "
            "unexpectedly long generations."
        ),
    )

    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=600,
        description="Maximum request duration.",
    )

    max_retries: int = Field(
        default=1,
        ge=0,
        le=10,
        description="Automatic provider retries.",
    )

    @field_validator(
        "model_name",
        "api_key",
    )
    @classmethod
    def normalize_required_strings(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("Required LLM configuration value cannot be empty.")

        return normalized

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().rstrip("/")

        return normalized or None
