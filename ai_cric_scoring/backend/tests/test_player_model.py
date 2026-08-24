import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError
from app.models.enums import BattingStyle, BowlingStyle, PlayerRole
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.services.player import PlayerService


@pytest.mark.asyncio
async def test_player_belongs_to_owner_and_enums_persist(
    db_session: AsyncSession,
    user: User,
    player: Player,
) -> None:
    assert player.owner_user_id == user.id
    assert player.player_role is PlayerRole.BATTER
    assert player.batting_style is BattingStyle.UNKNOWN
    assert player.bowling_style is BowlingStyle.UNKNOWN

    loaded = await db_session.get(Player, player.id)
    assert loaded is not None
    assert loaded.player_role is PlayerRole.BATTER


@pytest.mark.asyncio
async def test_player_can_join_team(
    db_session: AsyncSession,
    team: Team,
    player: Player,
) -> None:
    membership = await PlayerService(db_session).add_to_team(team_id=team.id, player_id=player.id)
    assert membership.team_id == team.id
    assert membership.player_id == player.id
    assert membership.is_active is True

    result = await db_session.execute(select(Team).options(selectinload(Team.memberships)).where(Team.id == team.id))
    loaded_team = result.scalar_one()
    assert len(loaded_team.memberships) == 1
    assert loaded_team.memberships[0].player_id == player.id


@pytest.mark.asyncio
async def test_duplicate_team_membership_is_rejected(
    db_session: AsyncSession,
    team: Team,
    player: Player,
) -> None:
    service = PlayerService(db_session)
    await service.add_to_team(team_id=team.id, player_id=player.id)
    with pytest.raises(ConflictError):
        await service.add_to_team(team_id=team.id, player_id=player.id)


@pytest.mark.asyncio
async def test_player_team_memberships_relationship(
    db_session: AsyncSession,
    team: Team,
    player: Player,
) -> None:
    await PlayerService(db_session).add_to_team(team_id=team.id, player_id=player.id)
    result = await db_session.execute(
        select(Player).options(selectinload(Player.team_memberships)).where(Player.id == player.id)
    )
    loaded = result.scalar_one()
    assert len(loaded.team_memberships) == 1
    assert loaded.team_memberships[0].team_id == team.id
