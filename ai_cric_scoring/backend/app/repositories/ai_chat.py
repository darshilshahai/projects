from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.repositories.base import BaseRepository


class AIConversationRepository(BaseRepository[AIConversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AIConversation)

    async def get_for_user_match(self, user_id: uuid.UUID, match_id: uuid.UUID) -> AIConversation | None:
        stmt = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.match_id == match_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class AIMessageRepository(BaseRepository[AIMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AIMessage)

    async def get_by_client_id(self, conversation_id: uuid.UUID, client_message_id: uuid.UUID) -> AIMessage | None:
        stmt = select(AIMessage).where(
            AIMessage.conversation_id == conversation_id,
            AIMessage.client_message_id == client_message_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_page(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int,
        before_id: uuid.UUID | None,
    ) -> list[AIMessage]:
        stmt = select(AIMessage).where(AIMessage.conversation_id == conversation_id)
        if before_id is not None:
            current = await self.get_by_id(before_id)
            if current is None or current.conversation_id != conversation_id:
                return []
            stmt = stmt.where(
                (AIMessage.created_at < current.created_at)
                | ((AIMessage.created_at == current.created_at) & (AIMessage.id < current.id))
            )
        stmt = stmt.order_by(AIMessage.created_at.desc(), AIMessage.id.desc()).limit(limit + 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def latest(self, conversation_id: uuid.UUID, limit: int) -> list[AIMessage]:
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.desc(), AIMessage.id.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        rows.reverse()
        return rows

    async def next_assistant(self, conversation_id: uuid.UUID, after: AIMessage) -> AIMessage | None:
        stmt = (
            select(AIMessage)
            .where(
                AIMessage.conversation_id == conversation_id,
                AIMessage.role == "ASSISTANT",
                (AIMessage.created_at > after.created_at)
                | ((AIMessage.created_at == after.created_at) & (AIMessage.id > after.id)),
            )
            .order_by(AIMessage.created_at.asc(), AIMessage.id.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
