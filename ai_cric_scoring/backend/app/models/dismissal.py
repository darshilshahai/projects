from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin
from app.models.enums import DismissalType, pg_enum

if TYPE_CHECKING:
    from app.models.delivery import Delivery
    from app.models.match_player import MatchPlayer


class Dismissal(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "dismissals"
    __table_args__ = (UniqueConstraint("delivery_id", name="uq_dismissals_delivery"),)

    delivery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False)
    dismissed_player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_players.id", ondelete="CASCADE"),
        nullable=False,
    )
    dismissal_type: Mapped[DismissalType] = mapped_column(
        pg_enum(DismissalType, "dismissal_type"),
        nullable=False,
    )
    fielder_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("match_players.id", ondelete="CASCADE"))
    credited_to_bowler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    delivery: Mapped[Delivery] = relationship(back_populates="dismissal", lazy="raise")
    dismissed_player: Mapped[MatchPlayer] = relationship(foreign_keys=[dismissed_player_id], lazy="raise")
    fielder: Mapped[MatchPlayer | None] = relationship(foreign_keys=[fielder_id], lazy="raise")
