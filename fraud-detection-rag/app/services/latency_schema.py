from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class RAGLatency:
    """
    Time spent in the main RAG processing stages.

    All values are stored in milliseconds.
    """

    retrieval_ms: float
    prompt_building_ms: float
    llm_generation_ms: float
    source_building_ms: float
    total_ms: float

    def __post_init__(self) -> None:
        values = {
            "retrieval_ms": self.retrieval_ms,
            "prompt_building_ms": self.prompt_building_ms,
            "llm_generation_ms": self.llm_generation_ms,
            "source_building_ms": self.source_building_ms,
            "total_ms": self.total_ms,
        }

        for field_name, value in values.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{field_name} must be numeric, received {type(value).__name__}."
                )

            if not math.isfinite(float(value)):
                raise ValueError(f"{field_name} must be finite.")

            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")
