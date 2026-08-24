from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ai_message import AIMessage
    from app.models.match import Match
    from app.models.user import User


class AIConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_ai_conversations_user_match"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    pending_question: Mapped[str | None] = mapped_column(String(1000))
    last_player_id: Mapped[uuid.UUID | None] = mapped_column()
    last_team_id: Mapped[uuid.UUID | None] = mapped_column()
    last_innings_number: Mapped[int | None] = mapped_column()

    user: Mapped[User] = relationship(lazy="raise")
    match: Mapped[Match] = relationship(lazy="raise")
    messages: Mapped[list[AIMessage]] = relationship(lazy="raise")
