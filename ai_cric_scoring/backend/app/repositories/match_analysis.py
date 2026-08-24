from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_analysis import MatchAnalysis
from app.repositories.base import BaseRepository


class MatchAnalysisRepository(BaseRepository[MatchAnalysis]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MatchAnalysis)

    async def get_latest(self, match_id: uuid.UUID) -> MatchAnalysis | None:
        stmt = (
            select(MatchAnalysis)
            .where(MatchAnalysis.match_id == match_id)
            .order_by(
                MatchAnalysis.created_at.desc(),
                MatchAnalysis.updated_at.desc(),
                MatchAnalysis.id.desc(),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def refresh(self, entity: MatchAnalysis) -> MatchAnalysis:
        await self._session.refresh(entity)
        return entity
