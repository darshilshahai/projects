from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery import Delivery
from app.models.dismissal import Dismissal
from app.models.innings import Innings
from app.models.innings_stats import InningsBattingStat, InningsBowlingStat
from app.models.score_snapshot import ScoreSnapshot
from app.models.scoring_event import ScoringEvent
from app.repositories.base import BaseRepository


class InningsRepository(BaseRepository[Innings]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Innings)

    async def list_for_match(self, match_id: uuid.UUID) -> list[Innings]:
        stmt = select(Innings).where(Innings.match_id == match_id).order_by(Innings.innings_number)
        return list((await self._session.execute(stmt)).scalars())

    async def get_for_update(self, innings_id: uuid.UUID) -> Innings | None:
        stmt = select(Innings).where(Innings.id == innings_id).with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def delete(self, innings: Innings) -> None:
        await self._session.delete(innings)


class ScoringEventRepository(BaseRepository[ScoringEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ScoringEvent)

    async def get_by_client_event_id(self, match_id: uuid.UUID, client_event_id: uuid.UUID) -> ScoringEvent | None:
        stmt = select(ScoringEvent).where(
            ScoringEvent.match_id == match_id,
            ScoringEvent.client_event_id == client_event_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_innings(self, innings_id: uuid.UUID) -> list[ScoringEvent]:
        stmt = select(ScoringEvent).where(ScoringEvent.innings_id == innings_id).order_by(ScoringEvent.sequence_number)
        return list((await self._session.execute(stmt)).scalars())

    async def max_sequence(self, innings_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.coalesce(func.max(ScoringEvent.sequence_number), 0)).where(
                ScoringEvent.innings_id == innings_id
            )
        )
        return int(value or 0)


class DeliveryRepository(BaseRepository[Delivery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Delivery)

    async def get_by_event_id(self, scoring_event_id: uuid.UUID) -> Delivery | None:
        stmt = select(Delivery).where(Delivery.scoring_event_id == scoring_event_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_active_for_innings_ids(self, innings_ids: list[uuid.UUID]) -> list[Delivery]:
        if not innings_ids:
            return []
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.dismissal))
            .where(Delivery.innings_id.in_(innings_ids), Delivery.is_voided.is_(False))
            .order_by(Delivery.innings_id, Delivery.sequence_number)
        )
        return list((await self._session.execute(stmt)).scalars())


class DismissalRepository(BaseRepository[Dismissal]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Dismissal)


class ScoreSnapshotRepository(BaseRepository[ScoreSnapshot]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ScoreSnapshot)

    async def get_for_innings(self, innings_id: uuid.UUID) -> ScoreSnapshot | None:
        stmt = select(ScoreSnapshot).where(ScoreSnapshot.innings_id == innings_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_for_update(self, innings_id: uuid.UUID) -> ScoreSnapshot | None:
        stmt = select(ScoreSnapshot).where(ScoreSnapshot.innings_id == innings_id).with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_innings_ids(self, innings_ids: list[uuid.UUID]) -> list[ScoreSnapshot]:
        if not innings_ids:
            return []
        stmt = select(ScoreSnapshot).where(ScoreSnapshot.innings_id.in_(innings_ids))
        return list((await self._session.execute(stmt)).scalars())


class BattingStatsRepository(BaseRepository[InningsBattingStat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InningsBattingStat)

    async def list_for_innings(self, innings_id: uuid.UUID) -> list[InningsBattingStat]:
        stmt = select(InningsBattingStat).where(InningsBattingStat.innings_id == innings_id)
        return list((await self._session.execute(stmt)).scalars())

    async def list_for_innings_ids(self, innings_ids: list[uuid.UUID]) -> list[InningsBattingStat]:
        if not innings_ids:
            return []
        stmt = (
            select(InningsBattingStat)
            .where(InningsBattingStat.innings_id.in_(innings_ids))
            .order_by(InningsBattingStat.batting_position)
        )
        return list((await self._session.execute(stmt)).scalars())

    async def replace_for_innings(self, innings_id: uuid.UUID, rows: list[InningsBattingStat]) -> None:
        await self._session.execute(delete(InningsBattingStat).where(InningsBattingStat.innings_id == innings_id))
        for row in rows:
            self.add(row)


class BowlingStatsRepository(BaseRepository[InningsBowlingStat]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InningsBowlingStat)

    async def list_for_innings(self, innings_id: uuid.UUID) -> list[InningsBowlingStat]:
        stmt = select(InningsBowlingStat).where(InningsBowlingStat.innings_id == innings_id)
        return list((await self._session.execute(stmt)).scalars())

    async def list_for_innings_ids(self, innings_ids: list[uuid.UUID]) -> list[InningsBowlingStat]:
        if not innings_ids:
            return []
        stmt = select(InningsBowlingStat).where(InningsBowlingStat.innings_id.in_(innings_ids))
        return list((await self._session.execute(stmt)).scalars())

    async def replace_for_innings(self, innings_id: uuid.UUID, rows: list[InningsBowlingStat]) -> None:
        await self._session.execute(delete(InningsBowlingStat).where(InningsBowlingStat.innings_id == innings_id))
        for row in rows:
            self.add(row)


def utcnow() -> datetime:
    return datetime.now(UTC)
