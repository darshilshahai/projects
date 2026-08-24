from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PlayerNotFoundError
from app.models.enums import BattingStyle, BowlingStyle, PlayerRole
from app.models.player import Player
from app.models.team import Team
from app.models.team_player import TeamPlayer
from app.repositories.player import PlayerRepository
from app.repositories.team_player import TeamPlayerRepository
from app.services.persistence import flush_or_raise_conflict

MAX_PLAYER_NAME_LENGTH = 160


def normalize_player_name(name: str) -> str:
    normalized = " ".join(name.split())
    if not normalized:
        raise ValueError("Player name is required.")
    return normalized[:MAX_PLAYER_NAME_LENGTH]


class PlayerService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._players = PlayerRepository(session)
        self._memberships = TeamPlayerRepository(session)

    async def create(
        self,
        *,
        owner_user_id: uuid.UUID,
        name: str,
        player_role: PlayerRole,
        batting_style: BattingStyle = BattingStyle.UNKNOWN,
        bowling_style: BowlingStyle = BowlingStyle.UNKNOWN,
    ) -> Player:
        player = Player(
            owner_user_id=owner_user_id,
            name=normalize_player_name(name),
            player_role=player_role,
            batting_style=batting_style,
            bowling_style=bowling_style,
        )
        self._players.add(player)
        await self._players.flush()
        return player

    async def add_to_team(self, *, team_id: uuid.UUID, player_id: uuid.UUID) -> TeamPlayer:
        membership = TeamPlayer(team_id=team_id, player_id=player_id)
        self._memberships.add(membership)
        await flush_or_raise_conflict(self._session, "This player is already on the team roster.")
        return membership

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
        return await self._players.list_owned(
            owner_user_id,
            search=search,
            role=role,
            is_active=is_active,
            limit=min(max(limit, 1), 100),
            offset=max(offset, 0),
        )

    async def get_owned(self, player_id: uuid.UUID, owner_user_id: uuid.UUID) -> Player:
        player = await self._players.get_by_id_for_owner(player_id, owner_user_id)
        if player is None:
            raise PlayerNotFoundError()
        return player

    async def update_owned(
        self,
        player_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        *,
        name: str | None = None,
        player_role: PlayerRole | None = None,
        batting_style: BattingStyle | None = None,
        bowling_style: BowlingStyle | None = None,
        is_active: bool | None = None,
    ) -> Player:
        player = await self.get_owned(player_id, owner_user_id)
        if name is not None:
            player.name = normalize_player_name(name)
        if player_role is not None:
            player.player_role = player_role
        if batting_style is not None:
            player.batting_style = batting_style
        if bowling_style is not None:
            player.bowling_style = bowling_style
        if is_active is not None:
            player.is_active = is_active
        await self._session.flush()
        await self._session.refresh(player)
        return player

    async def list_active_teams(self, player_id: uuid.UUID) -> list[Team]:
        return await self._memberships.list_active_teams_for_player(player_id)

    async def get_by_id(self, player_id: uuid.UUID) -> Player:
        player = await self._players.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError()
        return player
