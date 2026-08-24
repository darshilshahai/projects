from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class QuoteOut(BaseModel):
    quote: str
    author: str
    date: str


class InspirationOut(BaseModel):
    quote: QuoteOut
    manifestations: list[str]
    source: Literal["user", "ai"]

    model_config = ConfigDict(populate_by_name=True)
