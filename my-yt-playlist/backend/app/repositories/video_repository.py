from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import asc, delete, desc, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.integrations.youtube import YouTubeVideoMetadata
from app.models.collection import Collection, CollectionVideo
from app.models.tag import Tag, UserVideoTag
from app.models.video import TimestampNote, UserVideo, Video


class VideoRepository:
    """Data Access Layer for Video, UserVideo, and TimestampNote entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_global_video_by_youtube_id(self, youtube_video_id: str) -> Optional[Video]:
        """Fetch global video record by 11-char YouTube ID."""
        query = select(Video).where(Video.youtube_video_id == youtube_video_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_global_video(self, metadata: YouTubeVideoMetadata) -> Video:
        """Create global YouTube video metadata record."""
        video = Video(
            youtube_video_id=metadata.youtube_video_id,
            youtube_url=metadata.youtube_url,
            title=metadata.title,
            description=metadata.description,
            channel_name=metadata.channel_name,
            channel_id=metadata.channel_id,
            thumbnail_url=metadata.thumbnail_url,
            duration_seconds=metadata.duration_seconds,
            published_at=metadata.published_at,
            category_id=metadata.category_id,
            is_unavailable=metadata.is_unavailable,
        )
        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        return video

    async def get_user_video_by_youtube_id(
        self, user_id: UUID, youtube_video_id: str
    ) -> Optional[UserVideo]:
        """Check if user has already saved a specific video by YouTube ID."""
        query = (
            select(UserVideo)
            .join(UserVideo.video)
            .options(
                joinedload(UserVideo.video),
                selectinload(UserVideo.timestamp_notes),
            )
            .where(
                UserVideo.user_id == user_id,
                Video.youtube_video_id == youtube_video_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_video_by_id(
        self, user_id: UUID, user_video_id: UUID
    ) -> Optional[UserVideo]:
        """
        Fetch single saved UserVideo record by ID.
        MANDATORY IDOR Protection: Enforces UserVideo.user_id == user_id!
        """
        query = (
            select(UserVideo)
            .options(
                joinedload(UserVideo.video),
                selectinload(UserVideo.timestamp_notes),
            )
            .where(
                UserVideo.id == user_video_id,
                UserVideo.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user_video(
        self,
        user_id: UUID,
        video_id: UUID,
        notes: Optional[str] = None,
        user_category: Optional[str] = None,
    ) -> UserVideo:
        """Create new UserVideo record linking user and global video."""
        user_video = UserVideo(
            user_id=user_id,
            video_id=video_id,
            status="unwatched",
            is_favourite=False,
            is_watch_later=False,
            user_category=user_category,
            notes=notes,
        )
        self.db.add(user_video)
        await self.db.commit()

        return await self.get_user_video_by_id(user_id, user_video.id)  # type: ignore

    async def update_user_video(
        self, user_video: UserVideo, update_data: dict
    ) -> UserVideo:
        """Update existing UserVideo state attributes."""
        for field, value in update_data.items():
            if hasattr(user_video, field) and value is not None:
                setattr(user_video, field, value)
        await self.db.commit()
        await self.db.refresh(user_video)
        return user_video

    async def delete_user_video(self, user_video: UserVideo) -> bool:
        """Delete UserVideo record from library."""
        await self.db.delete(user_video)
        await self.db.commit()
        return True

    async def add_timestamp_note(
        self, user_video_id: UUID, timestamp_seconds: int, note_text: str
    ) -> TimestampNote:
        """Create timestamp note for UserVideo."""
        note = TimestampNote(
            user_video_id=user_video_id,
            timestamp_seconds=timestamp_seconds,
            note_text=note_text,
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def delete_timestamp_note(
        self, user_video_id: UUID, note_id: UUID
    ) -> bool:
        """Delete timestamp note associated with UserVideo."""
        query = (
            delete(TimestampNote)
            .where(
                TimestampNote.id == note_id,
                TimestampNote.user_video_id == user_video_id,
            )
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

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
    ) -> Tuple[List[UserVideo], int]:
        """
        Query user's saved video library with multi-criteria filtering,
        full-text ILIKE search, sorting, and offset pagination.
        Returns Tuple of (items, total_count).
        """
        # Base query joining UserVideo and Video
        query = (
            select(UserVideo)
            .join(UserVideo.video)
            .options(
                joinedload(UserVideo.video),
                selectinload(UserVideo.timestamp_notes),
            )
            .where(UserVideo.user_id == user_id)
        )

        # Count query
        count_query = (
            select(func.count(distinct(UserVideo.id)))
            .select_from(UserVideo)
            .join(UserVideo.video)
            .where(UserVideo.user_id == user_id)
        )

        # Apply Filters
        if status:
            query = query.where(UserVideo.status == status)
            count_query = count_query.where(UserVideo.status == status)

        if is_favourite is not None:
            query = query.where(UserVideo.is_favourite == is_favourite)
            count_query = count_query.where(UserVideo.is_favourite == is_favourite)

        if is_watch_later is not None:
            query = query.where(UserVideo.is_watch_later == is_watch_later)
            count_query = count_query.where(UserVideo.is_watch_later == is_watch_later)

        if user_category:
            query = query.where(UserVideo.user_category == user_category)
            count_query = count_query.where(UserVideo.user_category == user_category)

        if channel_name:
            channel_filter = Video.channel_name.ilike(f"%{channel_name}%")
            query = query.where(channel_filter)
            count_query = count_query.where(channel_filter)

        if max_duration_seconds is not None:
            dur_filter = Video.duration_seconds <= max_duration_seconds
            query = query.where(dur_filter)
            count_query = count_query.where(dur_filter)

        if tag_id:
            query = query.join(UserVideo.tags).where(Tag.id == tag_id)
            count_query = count_query.join(UserVideo.tags).where(Tag.id == tag_id)

        if collection_id:
            query = query.join(UserVideo.collections).where(Collection.id == collection_id)
            count_query = count_query.join(UserVideo.collections).where(Collection.id == collection_id)

        if search_query:
            pattern = f"%{search_query.strip()}%"
            search_filter = or_(
                Video.title.ilike(pattern),
                Video.description.ilike(pattern),
                Video.channel_name.ilike(pattern),
                UserVideo.notes.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply Sorting
        order_func = desc if order == "desc" else asc
        if sort_by == "published_at":
            query = query.order_by(order_func(Video.published_at), order_func(UserVideo.added_at))
        elif sort_by == "title":
            query = query.order_by(order_func(Video.title))
        elif sort_by == "duration_seconds":
            query = query.order_by(order_func(Video.duration_seconds))
        else:  # default added_at
            query = query.order_by(order_func(UserVideo.added_at))

        # Total Count Execution
        total_count_res = await self.db.execute(count_query)
        total_items = total_count_res.scalar() or 0

        # Pagination Offset and Limit Execution
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        items = list(result.scalars().unique())
        return items, total_items

    async def get_quick_queue(
        self, user_id: UUID, max_duration_seconds: int, limit: int = 10
    ) -> List[UserVideo]:
        """
        Unique V1 Feature: Smart Duration Quick Queue.
        Retrieves unwatched videos fitting max_duration_seconds,
        prioritized by watch_later flag, favourite flag, and added_at date.
        """
        query = (
            select(UserVideo)
            .join(UserVideo.video)
            .options(
                joinedload(UserVideo.video),
                selectinload(UserVideo.timestamp_notes),
            )
            .where(
                UserVideo.user_id == user_id,
                UserVideo.status == "unwatched",
                Video.duration_seconds > 0,
                Video.duration_seconds <= max_duration_seconds,
            )
            .order_by(
                desc(UserVideo.is_watch_later),
                desc(UserVideo.is_favourite),
                desc(UserVideo.added_at),
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique())
