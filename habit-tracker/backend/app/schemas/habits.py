from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    daysOfWeek: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])

    model_config = ConfigDict(populate_by_name=True)


class HabitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    daysOfWeek: list[int] | None = None
    archived: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class HabitOut(BaseModel):
    id: UUID
    name: str
    daysOfWeek: list[int]
    archived: bool
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)
