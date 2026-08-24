from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TeamNotFoundError
from app.models.team import Team
from app.repositories.team import TeamRepository
from app.services.persistence import flush_or_raise_conflict

MAX_TEAM_NAME_LENGTH = 120
MAX_SHORT_NAME_LENGTH = 16


def normalize_team_name(name: str) -> str:
    normalized = " ".join(name.split())
    if not normalized:
        raise ValueError("Team name is required.")
    return normalized[:MAX_TEAM_NAME_LENGTH]


def normalize_short_name(short_name: str | None) -> str | None:
    if short_name is None:
        return None
    normalized = " ".join(short_name.split())
    if not normalized:
        return None
    return normalized[:MAX_SHORT_NAME_LENGTH]


class TeamService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)

    async def create(
        self,
        *,
        owner_user_id: uuid.UUID,
        name: str,
        short_name: str | None = None,
    ) -> Team:
        team = Team(
            owner_user_id=owner_user_id,
            name=normalize_team_name(name),
            short_name=normalize_short_name(short_name),
        )
        self._teams.add(team)
        await flush_or_raise_conflict(
            self._session,
            "You already have a team with this name.",
            code="TEAM_NAME_ALREADY_EXISTS",
        )
        return team

    async def list_owned(
        self,
        owner_user_id: uuid.UUID,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Team, int]], int]:
        return await self._teams.list_owned(
            owner_user_id,
            search=search,
            is_active=is_active,
            limit=min(max(limit, 1), 100),
            offset=max(offset, 0),
        )

    async def get_owned(self, team_id: uuid.UUID, owner_user_id: uuid.UUID) -> tuple[Team, int]:
        team = await self._teams.get_by_id_for_owner(team_id, owner_user_id)
        if team is None:
            raise TeamNotFoundError()
        count = await self._teams.active_roster_count(team.id)
        return team, count

    async def update_owned(
        self,
        team_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        *,
        name: str | None = None,
        short_name: str | None = None,
        is_active: bool | None = None,
        short_name_set: bool = False,
    ) -> tuple[Team, int]:
        team, _count = await self.get_owned(team_id, owner_user_id)
        if name is not None:
            team.name = normalize_team_name(name)
        if short_name_set:
            team.short_name = normalize_short_name(short_name)
        if is_active is not None:
            team.is_active = is_active
        await flush_or_raise_conflict(
            self._session,
            "You already have a team with this name.",
            code="TEAM_NAME_ALREADY_EXISTS",
        )
        await self._session.refresh(team)
        count = await self._teams.active_roster_count(team.id)
        return team, count

    async def get_by_id(self, team_id: uuid.UUID) -> Team:
        team = await self._teams.get_by_id(team_id)
        if team is None:
            raise TeamNotFoundError()
        return team
