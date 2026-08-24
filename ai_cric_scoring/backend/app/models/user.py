from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String, text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.player import Player
    from app.models.refresh_token import RefreshToken
    from app.models.team import Team


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(btrim(email)) > 0", name="ck_users_email_not_empty"),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    teams: Mapped[list[Team]] = relationship(
        back_populates="owner",
        lazy="raise",
        foreign_keys="Team.owner_user_id",
    )
    players: Mapped[list[Player]] = relationship(
        back_populates="owner",
        lazy="raise",
        foreign_keys="Player.owner_user_id",
    )
    matches: Mapped[list[Match]] = relationship(
        back_populates="created_by",
        lazy="raise",
        foreign_keys="Match.created_by_user_id",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        lazy="raise",
        cascade="all, delete-orphan",
    )
