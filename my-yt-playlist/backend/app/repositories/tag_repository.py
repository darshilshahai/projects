from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tag import Tag, UserVideoTag


class TagRepository:
    """Data Access Layer for Tag and UserVideoTag entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, user_id: UUID, name: str) -> Tag:
        """Create new tag for user."""
        tag = Tag(
            user_id=user_id,
            name=name.strip().lower(),
        )
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def get_by_id(self, user_id: UUID, tag_id: UUID) -> Optional[Tag]:
        """Fetch tag by ID with IDOR protection."""
        query = select(Tag).where(
            Tag.id == tag_id, Tag.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: UUID, name: str) -> Optional[Tag]:
        """Fetch tag by name for specific user."""
        query = select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == name.strip().lower(),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_tags(self, user_id: UUID) -> List[Tuple[Tag, int]]:
        """List user tags with video usage count aggregation."""
        query = (
            select(
                Tag,
                func.count(UserVideoTag.user_video_id).label("usage_count"),
            )
            .outerjoin(UserVideoTag, Tag.id == UserVideoTag.tag_id)
            .where(Tag.user_id == user_id)
            .group_by(Tag.id)
            .order_by(Tag.name.asc())
        )
        result = await self.db.execute(query)
        return list(result.all())

    async def delete_tag(self, tag: Tag) -> bool:
        """Delete tag record."""
        await self.db.delete(tag)
        await self.db.commit()
        return True

    async def is_tag_attached(self, user_video_id: UUID, tag_id: UUID) -> bool:
        """Check if tag is attached to user video."""
        query = select(UserVideoTag).where(
            UserVideoTag.user_video_id == user_video_id,
            UserVideoTag.tag_id == tag_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def attach_tag_to_video(self, user_video_id: UUID, tag_id: UUID) -> bool:
        """Attach tag to user video."""
        if await self.is_tag_attached(user_video_id, tag_id):
            return True

        uvt = UserVideoTag(
            user_video_id=user_video_id,
            tag_id=tag_id,
        )
        self.db.add(uvt)
        await self.db.commit()
        return True

    async def detach_tag_from_video(self, user_video_id: UUID, tag_id: UUID) -> bool:
        """Detach tag from user video."""
        query = delete(UserVideoTag).where(
            UserVideoTag.user_video_id == user_video_id,
            UserVideoTag.tag_id == tag_id,
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
