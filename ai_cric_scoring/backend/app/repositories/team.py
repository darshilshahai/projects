from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.team import Team
from app.models.team_player import TeamPlayer
from app.repositories.base import BaseRepository


def _active_roster_count() -> ColumnElement[int]:
    return (
        select(func.count())
        .where(TeamPlayer.team_id == Team.id, TeamPlayer.is_active.is_(True))
        .correlate(Team)
        .scalar_subquery()
    )


class TeamRepository(BaseRepository[Team]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Team)

    async def get_by_id_for_owner(self, team_id: uuid.UUID, owner_user_id: uuid.UUID) -> Team | None:
        stmt = select(Team).where(Team.id == team_id, Team.owner_user_id == owner_user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_owned(
        self,
        owner_user_id: uuid.UUID,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Team, int]], int]:
        filters = [Team.owner_user_id == owner_user_id]
        if is_active is not None:
            filters.append(Team.is_active.is_(is_active))
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(or_(Team.name.ilike(pattern), Team.short_name.ilike(pattern)))

        count_stmt = select(func.count()).select_from(Team).where(*filters)
        total = int(await self._session.scalar(count_stmt) or 0)

        stmt = (
            select(Team, _active_roster_count()).where(*filters).order_by(Team.name.asc()).limit(limit).offset(offset)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], int(row[1] or 0)) for row in rows], total

    async def active_roster_count(self, team_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(TeamPlayer.team_id == team_id, TeamPlayer.is_active.is_(True))
        return int(await self._session.scalar(stmt) or 0)
