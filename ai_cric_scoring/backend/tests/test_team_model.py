import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError
from app.models.team import Team
from app.models.user import User
from app.services.team import TeamService
from app.services.user import UserService


@pytest.mark.asyncio
async def test_team_belongs_to_user(db_session: AsyncSession, user: User, team: Team) -> None:
    assert team.owner_user_id == user.id
    loaded = await db_session.execute(select(User).options(selectinload(User.teams)).where(User.id == user.id))
    owner = loaded.scalar_one()
    assert len(owner.teams) == 1
    assert owner.teams[0].name == "Blue XI"


@pytest.mark.asyncio
async def test_same_owner_cannot_reuse_team_name(
    db_session: AsyncSession,
    user: User,
    team: Team,
) -> None:
    with pytest.raises(ConflictError):
        await TeamService(db_session).create(owner_user_id=user.id, name="Blue XI")


@pytest.mark.asyncio
async def test_different_owners_may_share_team_name(db_session: AsyncSession, team: Team) -> None:
    other = await UserService(db_session).create(
        email="other@example.com",
        password_hash="hashed",
    )
    copy = await TeamService(db_session).create(owner_user_id=other.id, name="Blue XI")
    assert copy.id != team.id
    assert copy.name == team.name
    assert copy.owner_user_id != team.owner_user_id
