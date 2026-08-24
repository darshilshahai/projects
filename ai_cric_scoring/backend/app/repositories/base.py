from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[T: Base]:
    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    def add(self, entity: T) -> T:
        self._session.add(entity)
        return entity

    async def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        return await self._session.get(self._model, entity_id)

    async def flush(self) -> None:
        await self._session.flush()
