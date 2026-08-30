from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import PaginationMeta


class VideoCreateRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL (watch, short, embed, or youtu.be)")


class VideoUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, description="Watch status: unwatched, watching, watched")
    is_favourite: Optional[bool] = Field(None, description="Favorite flag")
    is_watch_later: Optional[bool] = Field(None, description="Watch later flag")
    user_category: Optional[str] = Field(None, max_length=100, description="Custom category label")
    notes: Optional[str] = Field(None, description="Personal video notes")


class TimestampNoteCreateRequest(BaseModel):
    timestamp_seconds: int = Field(..., ge=0, description="Timestamp in seconds")
    note_text: str = Field(..., min_length=1, description="Note content at timestamp")


class TimestampNoteResponse(BaseModel):
    id: UUID
    user_video_id: UUID
    timestamp_seconds: int
    note_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlobalVideoResponse(BaseModel):
    id: UUID
    youtube_video_id: str
    youtube_url: str
    title: str
    description: Optional[str] = None
    channel_name: str
    channel_id: str
    thumbnail_url: Optional[str] = None
    duration_seconds: int
    published_at: Optional[datetime] = None
    category_id: Optional[str] = None
    is_unavailable: bool

    model_config = ConfigDict(from_attributes=True)


class UserVideoResponse(BaseModel):
    id: UUID
    user_id: UUID
    video_id: UUID
    status: str
    is_favourite: bool
    is_watch_later: bool
    user_category: Optional[str] = None
    notes: Optional[str] = None
    added_at: datetime
    watched_at: Optional[datetime] = None
    updated_at: datetime
    video: GlobalVideoResponse
    timestamp_notes: List[TimestampNoteResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedUserVideoResponse(BaseModel):
    items: List[UserVideoResponse]
    meta: PaginationMeta
