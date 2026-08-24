from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.cricket.types import ScoringEventType


@dataclass(frozen=True)
class DomainEvent:
    type: ScoringEventType
    payload: dict[str, Any] = field(default_factory=dict)
    sequence_number: int | None = None
