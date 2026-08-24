from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.persistence import flush_or_raise_conflict


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str | None = None,
    ) -> User:
        user = User(email=email, password_hash=password_hash, display_name=display_name)
        self._users.add(user)
        await flush_or_raise_conflict(self._session, "A user with this email already exists.")
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("User not found.")
        return user
