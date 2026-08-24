from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InactivePlayerError,
    InactiveTeamError,
    PlayerAlreadyInTeamError,
    PlayerNotFoundError,
    PlayerNotInTeamError,
    TeamNotFoundError,
)
from app.models.team_player import TeamPlayer
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.repositories.team_player import TeamPlayerRepository


class RosterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)
        self._players = PlayerRepository(session)
        self._memberships = TeamPlayerRepository(session)

    async def list_roster(
        self,
        team_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> list[TeamPlayer]:
        team = await self._teams.get_by_id_for_owner(team_id, owner_user_id)
        if team is None:
            raise TeamNotFoundError()
        return await self._memberships.list_roster(team_id, include_inactive=include_inactive)

    async def add_player(
        self,
        team_id: uuid.UUID,
        player_id: uuid.UUID,
        owner_user_id: uuid.UUID,
    ) -> TeamPlayer:
        team = await self._teams.get_by_id_for_owner(team_id, owner_user_id)
        if team is None:
            raise TeamNotFoundError()
        player = await self._players.get_by_id_for_owner(player_id, owner_user_id)
        if player is None:
            raise PlayerNotFoundError()
        if not team.is_active:
            raise InactiveTeamError()
        if not player.is_active:
            raise InactivePlayerError()

        membership = await self._memberships.get_membership(team_id, player_id)
        if membership is None:
            membership = TeamPlayer(team_id=team_id, player_id=player_id)
            self._memberships.add(membership)
            await self._session.flush()
            loaded = await self._memberships.get_membership(team_id, player_id, load_player=True)
            assert loaded is not None
            return loaded
        if membership.is_active:
            raise PlayerAlreadyInTeamError()
        membership.is_active = True
        membership.left_at = None
        await self._session.flush()
        loaded = await self._memberships.get_membership(team_id, player_id, load_player=True)
        assert loaded is not None
        return loaded

    async def remove_player(
        self,
        team_id: uuid.UUID,
        player_id: uuid.UUID,
        owner_user_id: uuid.UUID,
    ) -> None:
        team = await self._teams.get_by_id_for_owner(team_id, owner_user_id)
        if team is None:
            raise TeamNotFoundError()
        membership = await self._memberships.get_membership(team_id, player_id)
        if membership is None or not membership.is_active:
            raise PlayerNotInTeamError()
        membership.is_active = False
        membership.left_at = datetime.now(UTC)
        await self._session.flush()
