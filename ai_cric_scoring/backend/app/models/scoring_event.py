from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint, false, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin
from app.models.enums import ScoringEventType, pg_enum

if TYPE_CHECKING:
    from app.models.innings import Innings
    from app.models.match import Match
    from app.models.user import User


class ScoringEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scoring_events"
    __table_args__ = (
        UniqueConstraint("innings_id", "sequence_number", name="uq_scoring_events_innings_sequence"),
        Index(
            "uq_scoring_events_match_client_event",
            "match_id",
            "client_event_id",
            unique=True,
            postgresql_where=text("client_event_id IS NOT NULL"),
        ),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    client_event_id: Mapped[uuid.UUID | None] = mapped_column()
    base_revision: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[ScoringEventType] = mapped_column(
        pg_enum(ScoringEventType, "scoring_event_type"),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    match: Mapped[Match] = relationship(lazy="raise")
    innings: Mapped[Innings] = relationship(back_populates="events", lazy="raise")
    created_by: Mapped[User] = relationship(lazy="raise")
