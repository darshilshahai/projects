from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    service: str
    environment: str
    database: Literal["connected", "disconnected"]
