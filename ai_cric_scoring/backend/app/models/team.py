from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.match_team import MatchTeam
    from app.models.team_player import TeamPlayer
    from app.models.user import User


class Team(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "name", name="uq_teams_owner_name"),
        CheckConstraint("length(btrim(name)) > 0", name="ck_teams_name_not_empty"),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    owner: Mapped[User] = relationship(back_populates="teams", lazy="raise", foreign_keys=[owner_user_id])
    memberships: Mapped[list[TeamPlayer]] = relationship(back_populates="team", lazy="raise")
    match_appearances: Mapped[list[MatchTeam]] = relationship(back_populates="team", lazy="raise")
