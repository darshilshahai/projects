from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import InningsStatus, pg_enum

if TYPE_CHECKING:
    from app.models.delivery import Delivery
    from app.models.innings_stats import InningsBattingStat, InningsBowlingStat
    from app.models.match import Match
    from app.models.match_team import MatchTeam
    from app.models.score_snapshot import ScoreSnapshot
    from app.models.scoring_event import ScoringEvent


class Innings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "innings"
    __table_args__ = (
        UniqueConstraint("match_id", "innings_number", name="uq_innings_match_number"),
        Index("ix_innings_batting_match_team_id_match_id", "batting_match_team_id", "match_id"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batting_match_team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_teams.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bowling_match_team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_teams.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[InningsStatus] = mapped_column(
        pg_enum(InningsStatus, "innings_status"),
        nullable=False,
        default=InningsStatus.NOT_STARTED,
    )
    target_runs: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    match: Mapped[Match] = relationship(back_populates="innings", lazy="raise")
    batting_match_team: Mapped[MatchTeam] = relationship(
        foreign_keys=[batting_match_team_id],
        lazy="raise",
    )
    bowling_match_team: Mapped[MatchTeam] = relationship(
        foreign_keys=[bowling_match_team_id],
        lazy="raise",
    )
    events: Mapped[list[ScoringEvent]] = relationship(back_populates="innings", lazy="raise")
    deliveries: Mapped[list[Delivery]] = relationship(back_populates="innings", lazy="raise")
    snapshot: Mapped[ScoreSnapshot | None] = relationship(back_populates="innings", lazy="raise", uselist=False)
    batting_stats: Mapped[list[InningsBattingStat]] = relationship(back_populates="innings", lazy="raise")
    bowling_stats: Mapped[list[InningsBowlingStat]] = relationship(back_populates="innings", lazy="raise")
