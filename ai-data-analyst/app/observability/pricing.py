from dataclasses import dataclass

from app.core.config import Settings
from app.observability.usage import TokenUsage


@dataclass(frozen=True)
class UsageCost:
    input_cost_usd: float
    cached_input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


class PricingCalculator:
    TOKENS_PER_MILLION = 1_000_000

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self._input_price = settings.openai_input_price_per_million

        self._cached_input_price = settings.openai_cached_input_price_per_million

        self._output_price = settings.openai_output_price_per_million

    def calculate(
        self,
        usage: TokenUsage,
    ) -> UsageCost:
        uncached_input_tokens = max(
            usage.input_tokens - usage.cached_input_tokens,
            0,
        )

        input_cost = uncached_input_tokens / self.TOKENS_PER_MILLION * self._input_price

        cached_input_cost = (
            usage.cached_input_tokens
            / self.TOKENS_PER_MILLION
            * self._cached_input_price
        )

        output_cost = usage.output_tokens / self.TOKENS_PER_MILLION * self._output_price

        total_cost = input_cost + cached_input_cost + output_cost

        return UsageCost(
            input_cost_usd=round(
                input_cost,
                8,
            ),
            cached_input_cost_usd=round(
                cached_input_cost,
                8,
            ),
            output_cost_usd=round(
                output_cost,
                8,
            ),
            total_cost_usd=round(
                total_cost,
                8,
            ),
        )
