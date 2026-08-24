import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == normalized)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_teams(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).options(selectinload(User.teams)).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
