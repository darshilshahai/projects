from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


RAGStreamEventName = Literal[
    "metadata",
    "token",
    "complete",
    "error",
]


@dataclass(frozen=True, slots=True)
class RAGStreamEvent:
    """
    One event emitted by the RAG streaming service.
    """

    event: RAGStreamEventName
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the event into a serializable dictionary.
        """

        return {
            "event": self.event,
            "data": self.data,
        }


@dataclass(frozen=True, slots=True)
class StreamingLatency:
    """
    Important streaming latency measurements.

    All values are in milliseconds.
    """

    retrieval_ms: float
    prompt_building_ms: float
    time_to_first_token_ms: float | None
    llm_generation_ms: float
    source_building_ms: float
    total_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)