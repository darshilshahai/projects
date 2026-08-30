from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")


class TagResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    usage_count: int = 0

    model_config = ConfigDict(from_attributes=True)
