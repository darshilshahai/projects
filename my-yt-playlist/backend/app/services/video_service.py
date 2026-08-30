import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    DuplicateResourceException,
    NotFoundException,
)
from app.integrations.youtube import YouTubeClient, YouTubeURLParser
from app.models.video import TimestampNote, UserVideo
from app.repositories.video_repository import VideoRepository
from app.schemas.common import PaginationMeta
from app.schemas.video import (
    PaginatedUserVideoResponse,
    TimestampNoteCreateRequest,
    UserVideoResponse,
    VideoCreateRequest,
    VideoUpdateRequest,
)


class VideoService:
    """Service layer for Video Ingestion, Querying, Search, and Library operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.youtube_client = YouTubeClient()

    async def add_video(self, user_id: UUID, data: VideoCreateRequest) -> UserVideo:
        """Ingest video by YouTube URL into user's library."""
        video_id_str = YouTubeURLParser.extract_video_id(data.url)

        existing_uv = await self.video_repo.get_user_video_by_youtube_id(
            user_id, video_id_str
        )
        if existing_uv:
            raise DuplicateResourceException("Video is already saved in your library.")

        global_video = await self.video_repo.get_global_video_by_youtube_id(video_id_str)
        if not global_video:
            metadata = await self.youtube_client.fetch_video_metadata(video_id_str)
            global_video = await self.video_repo.create_global_video(metadata)

        user_video = await self.video_repo.create_user_video(
            user_id=user_id,
            video_id=global_video.id,
        )
        return user_video

    async def get_video_details(self, user_id: UUID, user_video_id: UUID) -> UserVideo:
        """Fetch single saved video details with IDOR ownership validation."""
        user_video = await self.video_repo.get_user_video_by_id(user_id, user_video_id)
        if not user_video:
            raise NotFoundException("Video not found in your library.")
        return user_video

    async def update_video(
        self, user_id: UUID, user_video_id: UUID, data: VideoUpdateRequest
    ) -> UserVideo:
        """Update user video state (status, notes, favorite, watch-later)."""
        user_video = await self.get_video_details(user_id, user_video_id)

        update_dict = data.model_dump(exclude_unset=True)

        if update_dict.get("status") == "watched" and user_video.status != "watched":
            update_dict["watched_at"] = datetime.now(timezone.utc)
        elif update_dict.get("status") and update_dict["status"] != "watched":
            update_dict["watched_at"] = None

        updated = await self.video_repo.update_user_video(user_video, update_dict)
        return updated

    async def delete_video(self, user_id: UUID, user_video_id: UUID) -> bool:
        """Remove video from user library with IDOR validation."""
        user_video = await self.get_video_details(user_id, user_video_id)
        return await self.video_repo.delete_user_video(user_video)

    async def add_timestamp_note(
        self, user_id: UUID, user_video_id: UUID, data: TimestampNoteCreateRequest
    ) -> TimestampNote:
        """Add time-linked note to user video."""
        await self.get_video_details(user_id, user_video_id)  # Enforces ownership
        return await self.video_repo.add_timestamp_note(
            user_video_id=user_video_id,
            timestamp_seconds=data.timestamp_seconds,
            note_text=data.note_text,
        )

    async def delete_timestamp_note(
        self, user_id: UUID, user_video_id: UUID, note_id: UUID
    ) -> bool:
        """Delete time-linked note from user video."""
        await self.get_video_details(user_id, user_video_id)  # Enforces ownership
        deleted = await self.video_repo.delete_timestamp_note(user_video_id, note_id)
        if not deleted:
            raise NotFoundException("Timestamp note not found.")
        return True

    async def list_user_videos(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 10,
        sort_by: str = "added_at",
        order: str = "desc",
        status: Optional[str] = None,
        is_favourite: Optional[bool] = None,
        is_watch_later: Optional[bool] = None,
        user_category: Optional[str] = None,
        channel_name: Optional[str] = None,
        tag_id: Optional[UUID] = None,
        collection_id: Optional[UUID] = None,
        max_duration_seconds: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> PaginatedUserVideoResponse:
        """
        Query user's library with filtering, full-text search, sorting, and pagination.
        """
        items, total_items = await self.video_repo.list_user_videos(
            user_id=user_id,
            page=page,
            size=size,
            sort_by=sort_by,
            order=order,
            status=status,
            is_favourite=is_favourite,
            is_watch_later=is_watch_later,
            user_category=user_category,
            channel_name=channel_name,
            tag_id=tag_id,
            collection_id=collection_id,
            max_duration_seconds=max_duration_seconds,
            search_query=search_query,
        )

        total_pages = math.ceil(total_items / size) if total_items > 0 else 0
        meta = PaginationMeta(
            total_items=total_items,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        # Convert ORM items to Pydantic UserVideoResponse
        response_items = [UserVideoResponse.model_validate(item) for item in items]
        return PaginatedUserVideoResponse(items=response_items, meta=meta)

    async def get_quick_queue(
        self, user_id: UUID, max_duration_seconds: int, limit: int = 10
    ) -> List[UserVideo]:
        """Retrieve unwatched videos fitting max_duration_seconds window."""
        return await self.video_repo.get_quick_queue(
            user_id=user_id,
            max_duration_seconds=max_duration_seconds,
            limit=limit,
        )
