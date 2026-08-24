from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MatchFormat, MatchStatus, ResultType, TossDecision, pg_enum

if TYPE_CHECKING:
    from app.models.innings import Innings
    from app.models.match_player import MatchPlayer
    from app.models.match_team import MatchTeam
    from app.models.user import User


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("overs_per_innings > 0", name="ck_matches_overs_per_innings_positive"),
        CheckConstraint("balls_per_over > 0", name="ck_matches_balls_per_over_positive"),
        CheckConstraint(
            "players_per_team >= 2 AND players_per_team <= 11",
            name="ck_matches_players_per_team_range",
        ),
        Index("ix_matches_created_by_created_at", "created_by_user_id", "created_at"),
        Index("ix_matches_created_by_status_completed_at", "created_by_user_id", "status", "completed_at"),
    )

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(200))
    format: Mapped[MatchFormat] = mapped_column(pg_enum(MatchFormat, "match_format"), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(
        pg_enum(MatchStatus, "match_status"),
        nullable=False,
        default=MatchStatus.DRAFT,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    venue_name: Mapped[str | None] = mapped_column(String(200))
    overs_per_innings: Mapped[int] = mapped_column(Integer, nullable=False)
    balls_per_over: Mapped[int] = mapped_column(Integer, nullable=False, default=6, server_default="6")
    players_per_team: Mapped[int] = mapped_column(Integer, nullable=False, default=11, server_default="11")
    toss_winner_match_team_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    toss_decision: Mapped[TossDecision | None] = mapped_column(pg_enum(TossDecision, "toss_decision"))
    result_type: Mapped[ResultType | None] = mapped_column(pg_enum(ResultType, "result_type"))
    winner_match_team_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    margin_runs: Mapped[int | None] = mapped_column(Integer)
    margin_wickets: Mapped[int | None] = mapped_column(Integer)

    created_by: Mapped[User] = relationship(
        back_populates="matches",
        lazy="raise",
        foreign_keys=[created_by_user_id],
    )
    match_teams: Mapped[list[MatchTeam]] = relationship(
        back_populates="match",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    match_players: Mapped[list[MatchPlayer]] = relationship(
        back_populates="match",
        lazy="raise",
        cascade="all, delete-orphan",
    )
    innings: Mapped[list[Innings]] = relationship(
        back_populates="match",
        lazy="raise",
        cascade="all, delete-orphan",
    )
