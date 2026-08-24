from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import BattingStyle, BowlingStyle, PlayerRole


class RosterAddRequest(BaseModel):
    player_id: UUID


class RosterPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: UUID
    player_id: UUID
    name: str
    player_role: PlayerRole
    batting_style: BattingStyle
    bowling_style: BowlingStyle
    is_active: bool
    joined_at: datetime
    left_at: datetime | None


class RosterListResponse(BaseModel):
    items: list[RosterPlayerResponse]
    total: int
