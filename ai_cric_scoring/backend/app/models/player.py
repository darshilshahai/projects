from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BattingStyle, BowlingStyle, PlayerRole, pg_enum

if TYPE_CHECKING:
    from app.models.match_player import MatchPlayer
    from app.models.team_player import TeamPlayer
    from app.models.user import User


class Player(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "players"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="ck_players_name_not_empty"),
        Index("ix_players_owner_user_id", "owner_user_id"),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    player_role: Mapped[PlayerRole] = mapped_column(pg_enum(PlayerRole, "player_role"), nullable=False)
    batting_style: Mapped[BattingStyle] = mapped_column(
        pg_enum(BattingStyle, "batting_style"),
        nullable=False,
        default=BattingStyle.UNKNOWN,
    )
    bowling_style: Mapped[BowlingStyle] = mapped_column(
        pg_enum(BowlingStyle, "bowling_style"),
        nullable=False,
        default=BowlingStyle.UNKNOWN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    owner: Mapped[User] = relationship(back_populates="players", lazy="raise", foreign_keys=[owner_user_id])
    team_memberships: Mapped[list[TeamPlayer]] = relationship(back_populates="player", lazy="raise")
    match_appearances: Mapped[list[MatchPlayer]] = relationship(back_populates="player", lazy="raise")
