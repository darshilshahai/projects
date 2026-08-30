from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.tag import TagCreateRequest, TagResponse


class TagService:
    """Service layer for Tagging management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TagRepository(db)
        self.video_repo = VideoRepository(db)

    async def create_tag(self, user_id: UUID, data: TagCreateRequest) -> TagResponse:
        """Create new tag for user."""
        clean_name = data.name.strip().lower()
        existing = await self.repo.get_by_name(user_id, clean_name)
        if existing:
            raise DuplicateResourceException(
                f"Tag with name '{clean_name}' already exists."
            )

        tag = await self.repo.create_tag(user_id=user_id, name=clean_name)
        return TagResponse(
            id=tag.id,
            user_id=tag.user_id,
            name=tag.name,
            created_at=tag.created_at,
            usage_count=0,
        )

    async def get_tag(self, user_id: UUID, tag_id: UUID) -> Tag:
        """Fetch single tag with IDOR protection."""
        tag = await self.repo.get_by_id(user_id, tag_id)
        if not tag:
            raise NotFoundException("Tag not found.")
        return tag

    async def list_tags(self, user_id: UUID) -> List[TagResponse]:
        """List all tags owned by user with usage counts."""
        results = await self.repo.list_tags(user_id)
        return [
            TagResponse(
                id=t.id,
                user_id=t.user_id,
                name=t.name,
                created_at=t.created_at,
                usage_count=count,
            )
            for t, count in results
        ]

    async def delete_tag(self, user_id: UUID, tag_id: UUID) -> bool:
        """Delete tag with IDOR validation."""
        tag = await self.get_tag(user_id, tag_id)
        return await self.repo.delete_tag(tag)

    async def attach_tag_to_video(
        self, user_id: UUID, user_video_id: UUID, tag_id: UUID
    ) -> bool:
        """Attach tag to user video with IDOR ownership validation on both entities."""
        await self.get_tag(user_id, tag_id)  # Validate tag ownership
        user_video = await self.video_repo.get_user_video_by_id(user_id, user_video_id)
        if not user_video:
            raise NotFoundException("Video not found in your library.")

        return await self.repo.attach_tag_to_video(user_video_id, tag_id)

    async def detach_tag_from_video(
        self, user_id: UUID, user_video_id: UUID, tag_id: UUID
    ) -> bool:
        """Detach tag from user video with IDOR ownership validation."""
        await self.get_tag(user_id, tag_id)  # Validate tag ownership
        user_video = await self.video_repo.get_user_video_by_id(user_id, user_video_id)
        if not user_video:
            raise NotFoundException("Video not found in your library.")

        return await self.repo.detach_tag_from_video(user_video_id, tag_id)
