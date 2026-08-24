from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.player import Player
from app.models.team import Team
from app.models.team_player import TeamPlayer
from app.repositories.base import BaseRepository


class TeamPlayerRepository(BaseRepository[TeamPlayer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TeamPlayer)

    async def get_membership(
        self,
        team_id: uuid.UUID,
        player_id: uuid.UUID,
        *,
        load_player: bool = False,
    ) -> TeamPlayer | None:
        stmt = select(TeamPlayer).where(TeamPlayer.team_id == team_id, TeamPlayer.player_id == player_id)
        if load_player:
            stmt = stmt.options(selectinload(TeamPlayer.player))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_roster(
        self,
        team_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> list[TeamPlayer]:
        stmt = select(TeamPlayer).options(selectinload(TeamPlayer.player)).where(TeamPlayer.team_id == team_id)
        if not include_inactive:
            stmt = stmt.where(TeamPlayer.is_active.is_(True))
        stmt = stmt.join(Player, Player.id == TeamPlayer.player_id).order_by(Player.name.asc())
        return list((await self._session.execute(stmt)).scalars())

    async def list_active_teams_for_player(self, player_id: uuid.UUID) -> list[Team]:
        stmt = (
            select(Team)
            .join(TeamPlayer, TeamPlayer.team_id == Team.id)
            .where(TeamPlayer.player_id == player_id, TeamPlayer.is_active.is_(True))
            .order_by(Team.name.asc())
        )
        return list((await self._session.execute(stmt)).scalars())
