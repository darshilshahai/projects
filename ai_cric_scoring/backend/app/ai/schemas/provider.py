from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredGeneration[T]:
    data: T
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
