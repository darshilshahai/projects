from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

CHAT_MESSAGE_MAX_LENGTH = 1000


class ChatEvidence(BaseModel):
    fact_id: str
    type: str
    label: str
    summary: str


class ChatClarificationOption(BaseModel):
    label: str
    message: str


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    answer_type: str | None = None
    question_type: str | None = None
    evidence: list[ChatEvidence] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    clarification_options: list[ChatClarificationOption] = Field(default_factory=list)
    used_ai: bool = False
    created_at: datetime
    client_message_id: uuid.UUID | None = None


class ChatGenerationError(BaseModel):
    code: str
    message: str


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]
    has_more: bool = False


class SendChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=CHAT_MESSAGE_MAX_LENGTH)
    client_message_id: uuid.UUID


class SendChatResponse(BaseModel):
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut | None = None
    generation_error: ChatGenerationError | None = None
