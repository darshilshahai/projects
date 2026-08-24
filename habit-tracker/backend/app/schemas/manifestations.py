from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ManifestationCreate(BaseModel):
    text: str = Field(min_length=1, max_length=160)


class ManifestationUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=160)


class ManifestationOut(BaseModel):
    id: UUID
    text: str
    createdAt: datetime

    model_config = ConfigDict(populate_by_name=True)
