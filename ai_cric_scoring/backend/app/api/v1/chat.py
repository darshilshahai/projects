from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.ai.services.match_chat_service import MatchChatService
from app.core.dependencies import get_current_user, get_match_chat_service
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, SendChatRequest, SendChatResponse

router = APIRouter(prefix="/matches", tags=["chat"])


@router.get("/{match_id}/chat/messages", response_model=ChatHistoryResponse)
async def list_match_chat_messages(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    chats: Annotated[MatchChatService, Depends(get_match_chat_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
    before: UUID | None = None,
) -> ChatHistoryResponse:
    return await chats.list_messages(match_id, user.id, limit=limit, before_id=before)


@router.post("/{match_id}/chat/messages", response_model=SendChatResponse)
async def send_match_chat_message(
    match_id: UUID,
    payload: SendChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    chats: Annotated[MatchChatService, Depends(get_match_chat_service)],
) -> SendChatResponse:
    return await chats.send_message(
        match_id,
        user.id,
        message=payload.message,
        client_message_id=payload.client_message_id,
    )
