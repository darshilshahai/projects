from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, false, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.dismissal import Dismissal
    from app.models.innings import Innings
    from app.models.match_player import MatchPlayer
    from app.models.scoring_event import ScoringEvent


class Delivery(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "deliveries"
    __table_args__ = (UniqueConstraint("innings_id", "sequence_number", name="uq_deliveries_innings_sequence"),)

    innings_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    scoring_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scoring_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ball_in_over: Mapped[int] = mapped_column(Integer, nullable=False)
    striker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"), nullable=False)
    non_striker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_players.id", ondelete="CASCADE"),
        nullable=False,
    )
    bowler_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"), nullable=False)
    runs_off_bat: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wides: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    byes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leg_byes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    penalty_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_legal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    is_voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    innings: Mapped[Innings] = relationship(back_populates="deliveries", lazy="raise")
    scoring_event: Mapped[ScoringEvent] = relationship(lazy="raise")
    striker: Mapped[MatchPlayer] = relationship(foreign_keys=[striker_id], lazy="raise")
    non_striker: Mapped[MatchPlayer] = relationship(foreign_keys=[non_striker_id], lazy="raise")
    bowler: Mapped[MatchPlayer] = relationship(foreign_keys=[bowler_id], lazy="raise")
    dismissal: Mapped[Dismissal | None] = relationship(back_populates="delivery", lazy="raise", uselist=False)
