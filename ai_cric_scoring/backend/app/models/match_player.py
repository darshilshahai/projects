from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.match_team import MatchTeam
    from app.models.player import Player


class MatchPlayer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "match_players"
    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_players_match_player"),
        Index("ix_match_players_player_id", "player_id"),
        Index("ix_match_players_match_team_id", "match_team_id"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    match_team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="RESTRICT"), nullable=False)
    display_name_snapshot: Mapped[str] = mapped_column(String(160), nullable=False)
    is_playing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    is_captain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_wicket_keeper: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    batting_position: Mapped[int | None] = mapped_column(Integer)

    match: Mapped[Match] = relationship(back_populates="match_players", lazy="raise")
    match_team: Mapped[MatchTeam] = relationship(back_populates="match_players", lazy="raise")
    player: Mapped[Player] = relationship(back_populates="match_appearances", lazy="raise")
