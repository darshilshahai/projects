from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin
from app.models.enums import MatchSide, pg_enum

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.match_player import MatchPlayer
    from app.models.team import Team


class MatchTeam(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "match_teams"
    __table_args__ = (
        UniqueConstraint("match_id", "side", name="uq_match_teams_match_side"),
        UniqueConstraint("match_id", "team_id", name="uq_match_teams_match_team"),
        Index("ix_match_teams_team_id", "team_id"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False)
    team_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    team_short_name_snapshot: Mapped[str | None] = mapped_column(String(16))
    side: Mapped[MatchSide] = mapped_column(pg_enum(MatchSide, "match_side"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    match: Mapped[Match] = relationship(back_populates="match_teams", lazy="raise")
    team: Mapped[Team] = relationship(back_populates="match_appearances", lazy="raise")
    match_players: Mapped[list[MatchPlayer]] = relationship(back_populates="match_team", lazy="raise")
