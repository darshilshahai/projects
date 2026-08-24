from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


HabitStatus = Literal["done", "not_done"]


class EntryUpsert(BaseModel):
    habitId: UUID
    date: date
    status: HabitStatus | None = None

    model_config = ConfigDict(populate_by_name=True)


class EntryOut(BaseModel):
    id: UUID
    habitId: UUID
    date: date
    status: HabitStatus
    createdAt: datetime | None = None

    model_config = ConfigDict(populate_by_name=True)
