from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.analytics.history.definitions import RECENT_APPEARANCES, clamp_last_n
from app.models.enums import MatchFormat


class HistoricalScope(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    format: MatchFormat | None = None
    team_id: UUID | None = None
    last_n: int | None = Field(default=None, ge=1, le=50)
    completed_only: bool = True

    def normalized(self) -> HistoricalScope:
        return self.model_copy(update={"last_n": clamp_last_n(self.last_n)})

    def with_recent(self) -> HistoricalScope:
        current = self.normalized()
        if current.last_n is not None:
            return current
        return current.model_copy(update={"last_n": RECENT_APPEARANCES})

    def describe(self, sample_matches: int) -> str:
        parts = [f"Across {sample_matches} completed match" + ("es" if sample_matches != 1 else "")]
        if self.last_n:
            parts = [f"In the last {self.last_n} appearance" + ("s" if self.last_n != 1 else "")]
        if self.format:
            parts.append(f"({self.format.value})")
        if self.date_from or self.date_to:
            parts.append("in the selected date range")
        return " ".join(parts) + "."
