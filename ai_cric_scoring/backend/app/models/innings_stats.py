from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.innings import Innings
    from app.models.match_player import MatchPlayer


class InningsBattingStat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "innings_batting_stats"
    __table_args__ = (UniqueConstraint("innings_id", "player_id", name="uq_innings_batting_stats_player"),)

    innings_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"), nullable=False)
    batting_position: Mapped[int] = mapped_column(Integer, nullable=False)
    runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sixes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="BATTING")
    dismissal_type: Mapped[str | None] = mapped_column(String(40))

    innings: Mapped[Innings] = relationship(back_populates="batting_stats", lazy="raise")
    player: Mapped[MatchPlayer] = relationship(lazy="raise")


class InningsBowlingStat(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "innings_bowling_stats"
    __table_args__ = (UniqueConstraint("innings_id", "player_id", name="uq_innings_bowling_stats_player"),)

    innings_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"), nullable=False)
    legal_balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wides: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    maidens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    innings: Mapped[Innings] = relationship(back_populates="bowling_stats", lazy="raise")
    player: Mapped[MatchPlayer] = relationship(lazy="raise")
