from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, case, delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import InningsStatus, MatchFormat, MatchStatus
from app.models.innings import Innings
from app.models.match import Match
from app.models.match_player import MatchPlayer
from app.models.match_team import MatchTeam
from app.models.score_snapshot import ScoreSnapshot
from app.repositories.base import BaseRepository
from app.schemas.match import MatchListScope


class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Match)

    def _owned_detail_stmt(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Select[tuple[Match]]:
        return (
            select(Match)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Match.match_teams).selectinload(MatchTeam.match_players).selectinload(MatchPlayer.player),
                selectinload(Match.match_players),
            )
            .where(Match.id == match_id, Match.created_by_user_id == user_id)
        )

    async def get_with_participants(self, match_id: uuid.UUID) -> Match | None:
        stmt = (
            select(Match)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Match.match_teams).selectinload(MatchTeam.match_players),
                selectinload(Match.match_players),
            )
            .where(Match.id == match_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owned_for_update(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match | None:
        stmt = select(Match).where(Match.id == match_id, Match.created_by_user_id == user_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owned(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match | None:
        stmt = select(Match).where(Match.id == match_id, Match.created_by_user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owned_with_participants(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match | None:
        result = await self._session.execute(self._owned_detail_stmt(match_id, user_id))
        return result.scalar_one_or_none()

    async def list_owned(
        self,
        user_id: uuid.UUID,
        *,
        status: MatchStatus | None = None,
        scope: MatchListScope | None = None,
        match_format: MatchFormat | None = None,
        team_id: uuid.UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Match], int]:
        filters = [Match.created_by_user_id == user_id]
        if status is not None:
            filters.append(Match.status == status)
        elif scope is MatchListScope.ACTIVE:
            filters.append(Match.status.in_((MatchStatus.LIVE, MatchStatus.READY, MatchStatus.DRAFT)))
        elif scope is MatchListScope.HISTORY:
            filters.append(Match.status == MatchStatus.COMPLETED)
        if match_format is not None:
            filters.append(Match.format == match_format)
        if team_id is not None:
            filters.append(
                exists().where(MatchTeam.match_id == Match.id, MatchTeam.team_id == team_id),
            )
        term = search.strip() if search else ""
        if term:
            pattern = f"%{term}%"
            filters.append(
                or_(
                    Match.name.ilike(pattern),
                    Match.venue_name.ilike(pattern),
                    exists().where(
                        MatchTeam.match_id == Match.id,
                        MatchTeam.team_name_snapshot.ilike(pattern),
                    ),
                )
            )
        history_dates = scope is MatchListScope.HISTORY or status is MatchStatus.COMPLETED
        date_field = Match.completed_at if history_dates else Match.created_at
        if date_from is not None:
            filters.append(date_field >= date_from)
        if date_to is not None:
            filters.append(date_field <= date_to)

        total = int(await self._session.scalar(select(func.count()).select_from(Match).where(*filters)) or 0)
        stmt = (
            select(Match)
            .options(selectinload(Match.match_teams))
            .where(*filters)
            .order_by(*self._order_for(scope=scope, status=status))
            .limit(limit)
            .offset(offset)
        )
        items = list((await self._session.execute(stmt)).scalars())
        return items, total

    def _order_for(
        self,
        *,
        scope: MatchListScope | None,
        status: MatchStatus | None,
    ) -> tuple:
        if scope is MatchListScope.HISTORY or status is MatchStatus.COMPLETED:
            return (Match.completed_at.desc().nulls_last(), Match.id.desc())
        if scope is MatchListScope.ACTIVE:
            priority = case(
                (Match.status == MatchStatus.LIVE, 0),
                (Match.status == MatchStatus.READY, 1),
                else_=2,
            )
            return (priority, Match.updated_at.desc(), Match.id.desc())
        return (Match.created_at.desc(), Match.id.desc())

    async def list_score_rows(
        self,
        match_ids: list[uuid.UUID],
    ) -> list[tuple[Innings, ScoreSnapshot | None]]:
        if not match_ids:
            return []
        stmt = (
            select(Innings, ScoreSnapshot)
            .outerjoin(ScoreSnapshot, ScoreSnapshot.innings_id == Innings.id)
            .where(Innings.match_id.in_(match_ids), Innings.status != InningsStatus.NOT_STARTED)
            .order_by(Innings.match_id, Innings.innings_number)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(innings, snapshot) for innings, snapshot in rows]


class MatchTeamRepository(BaseRepository[MatchTeam]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MatchTeam)

    async def list_for_match(self, match_id: uuid.UUID) -> list[MatchTeam]:
        stmt = select(MatchTeam).where(MatchTeam.match_id == match_id)
        return list((await self._session.execute(stmt)).scalars())

    async def delete_for_match(self, match_id: uuid.UUID) -> None:
        await self._session.execute(delete(MatchTeam).where(MatchTeam.match_id == match_id))


class MatchPlayerRepository(BaseRepository[MatchPlayer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MatchPlayer)

    async def delete_for_match_team(self, match_team_id: uuid.UUID) -> None:
        await self._session.execute(delete(MatchPlayer).where(MatchPlayer.match_team_id == match_team_id))

    async def delete_for_match(self, match_id: uuid.UUID) -> None:
        await self._session.execute(delete(MatchPlayer).where(MatchPlayer.match_id == match_id))

    async def list_player_ids_for_match(self, match_id: uuid.UUID) -> set[uuid.UUID]:
        stmt = select(MatchPlayer.player_id).where(MatchPlayer.match_id == match_id)
        return set((await self._session.execute(stmt)).scalars())
