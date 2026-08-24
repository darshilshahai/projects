from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.innings import Innings
    from app.models.match import Match
    from app.models.match_player import MatchPlayer


class ScoreSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "score_snapshots"
    __table_args__ = (UniqueConstraint("innings_id", name="uq_score_snapshots_innings"),)

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    legal_balls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    striker_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"))
    non_striker_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"))
    current_bowler_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"))
    previous_bowler_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"))
    needs_new_batter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    needs_new_bowler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    target_runs: Mapped[int | None] = mapped_column(Integer)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    match: Mapped[Match] = relationship(lazy="raise")
    innings: Mapped[Innings] = relationship(back_populates="snapshot", lazy="raise")
    striker: Mapped[MatchPlayer | None] = relationship(foreign_keys=[striker_id], lazy="raise")
    non_striker: Mapped[MatchPlayer | None] = relationship(foreign_keys=[non_striker_id], lazy="raise")
    current_bowler: Mapped[MatchPlayer | None] = relationship(foreign_keys=[current_bowler_id], lazy="raise")
    previous_bowler: Mapped[MatchPlayer | None] = relationship(foreign_keys=[previous_bowler_id], lazy="raise")
