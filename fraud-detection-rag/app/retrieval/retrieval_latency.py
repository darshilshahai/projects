from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class RetrievalLatency:
    """
    Time spent inside the retrieval pipeline.

    All latency values are stored in milliseconds.
    """

    query_embedding_ms: float
    vector_search_ms: float
    result_processing_ms: float
    total_ms: float

    def __post_init__(self) -> None:
        values = {
            "query_embedding_ms": self.query_embedding_ms,
            "vector_search_ms": self.vector_search_ms,
            "result_processing_ms": self.result_processing_ms,
            "total_ms": self.total_ms,
        }

        for field_name, value in values.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{field_name} must be numeric, received {type(value).__name__}."
                )

            if not math.isfinite(float(value)):
                raise ValueError(f"{field_name} must be a finite number.")

            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")
