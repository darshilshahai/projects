from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BattingStyle, BowlingStyle, PlayerRole
from app.schemas.team import TeamSummary


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    player_role: PlayerRole
    batting_style: BattingStyle = BattingStyle.UNKNOWN
    bowling_style: BowlingStyle = BowlingStyle.UNKNOWN

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Player name is required.")
        return value


class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    player_role: PlayerRole | None = None
    batting_style: BattingStyle | None = None
    bowling_style: BowlingStyle | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("Player name is required.")
        return value


class PlayerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    player_role: PlayerRole
    batting_style: BattingStyle
    bowling_style: BowlingStyle
    is_active: bool
    created_at: datetime
    updated_at: datetime
    teams: list[TeamSummary] = Field(default_factory=list)


class PlayerListResponse(BaseModel):
    items: list[PlayerPublic]
    total: int
