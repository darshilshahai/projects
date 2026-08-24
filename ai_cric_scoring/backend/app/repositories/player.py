from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlayerRole
from app.models.player import Player
from app.repositories.base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Player)

    async def get_by_id_for_owner(self, player_id: uuid.UUID, owner_user_id: uuid.UUID) -> Player | None:
        stmt = select(Player).where(Player.id == player_id, Player.owner_user_id == owner_user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_owned(
        self,
        owner_user_id: uuid.UUID,
        *,
        search: str | None = None,
        role: PlayerRole | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Player], int]:
        filters = [Player.owner_user_id == owner_user_id]
        if is_active is not None:
            filters.append(Player.is_active.is_(is_active))
        if role is not None:
            filters.append(Player.player_role == role)
        if search:
            filters.append(Player.name.ilike(f"%{search.strip()}%"))

        count_stmt = select(func.count()).select_from(Player).where(*filters)
        total = int(await self._session.scalar(count_stmt) or 0)
        stmt = select(Player).where(*filters).order_by(Player.name.asc()).limit(limit).offset(offset)
        players = list((await self._session.execute(stmt)).scalars())
        return players, total
