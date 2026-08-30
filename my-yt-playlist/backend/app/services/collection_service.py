from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DuplicateResourceException, NotFoundException
from app.models.collection import Collection
from app.repositories.collection_repository import CollectionRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionResponse,
    CollectionUpdateRequest,
)


class CollectionService:
    """Service layer for Custom Collections management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CollectionRepository(db)
        self.video_repo = VideoRepository(db)

    async def create_collection(
        self, user_id: UUID, data: CollectionCreateRequest
    ) -> CollectionResponse:
        """Create new custom collection for user."""
        existing = await self.repo.get_by_name(user_id, data.name)
        if existing:
            raise DuplicateResourceException(
                f"Collection with name '{data.name}' already exists."
            )

        collection = await self.repo.create_collection(
            user_id=user_id,
            name=data.name,
            description=data.description,
        )
        return CollectionResponse(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            description=collection.description,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            video_count=0,
        )

    async def get_collection(self, user_id: UUID, collection_id: UUID) -> Collection:
        """Fetch single collection with IDOR protection."""
        collection = await self.repo.get_by_id(user_id, collection_id)
        if not collection:
            raise NotFoundException("Collection not found.")
        return collection

    async def list_collections(self, user_id: UUID) -> List[CollectionResponse]:
        """List all collections owned by user with video counts."""
        results = await self.repo.list_collections(user_id)
        return [
            CollectionResponse(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                description=c.description,
                created_at=c.created_at,
                updated_at=c.updated_at,
                video_count=count,
            )
            for c, count in results
        ]

    async def update_collection(
        self, user_id: UUID, collection_id: UUID, data: CollectionUpdateRequest
    ) -> CollectionResponse:
        """Update collection name or description."""
        collection = await self.get_collection(user_id, collection_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "name" in update_dict:
            new_name = update_dict["name"]
            existing = await self.repo.get_by_name(user_id, new_name)
            if existing and existing.id != collection_id:
                raise DuplicateResourceException(
                    f"Collection with name '{new_name}' already exists."
                )

        updated = await self.repo.update_collection(collection, update_dict)
        # Fetch current video count
        _, count = (await self.repo.list_collections(user_id))[0]
        return CollectionResponse(
            id=updated.id,
            user_id=updated.user_id,
            name=updated.name,
            description=updated.description,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            video_count=count,
        )

    async def delete_collection(self, user_id: UUID, collection_id: UUID) -> bool:
        """Delete collection with IDOR validation."""
        collection = await self.get_collection(user_id, collection_id)
        return await self.repo.delete_collection(collection)

    async def add_video_to_collection(
        self, user_id: UUID, collection_id: UUID, user_video_id: UUID
    ) -> bool:
        """Add user video to collection with IDOR ownership validation on both entities."""
        await self.get_collection(user_id, collection_id)  # Validate collection ownership
        user_video = await self.video_repo.get_user_video_by_id(user_id, user_video_id)
        if not user_video:
            raise NotFoundException("Video not found in your library.")

        return await self.repo.add_video_to_collection(collection_id, user_video_id)

    async def remove_video_from_collection(
        self, user_id: UUID, collection_id: UUID, user_video_id: UUID
    ) -> bool:
        """Remove user video from collection with IDOR ownership validation."""
        await self.get_collection(user_id, collection_id)  # Validate collection ownership
        user_video = await self.video_repo.get_user_video_by_id(user_id, user_video_id)
        if not user_video:
            raise NotFoundException("Video not found in your library.")

        return await self.repo.remove_video_from_collection(collection_id, user_video_id)
