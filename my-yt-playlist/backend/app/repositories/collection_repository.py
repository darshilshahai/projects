from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.collection import Collection, CollectionVideo


class CollectionRepository:
    """Data Access Layer for Collection and CollectionVideo entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_collection(
        self, user_id: UUID, name: str, description: Optional[str] = None
    ) -> Collection:
        """Create new custom collection for user."""
        collection = Collection(
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
        )
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def get_by_id(self, user_id: UUID, collection_id: UUID) -> Optional[Collection]:
        """Fetch collection by ID with IDOR protection."""
        query = select(Collection).where(
            Collection.id == collection_id, Collection.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: UUID, name: str) -> Optional[Collection]:
        """Fetch collection by name for specific user."""
        query = select(Collection).where(
            Collection.user_id == user_id,
            func.lower(Collection.name) == name.strip().lower(),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_collections(self, user_id: UUID) -> List[Tuple[Collection, int]]:
        """List user collections with video count aggregation."""
        query = (
            select(
                Collection,
                func.count(CollectionVideo.user_video_id).label("video_count"),
            )
            .outerjoin(CollectionVideo, Collection.id == CollectionVideo.collection_id)
            .where(Collection.user_id == user_id)
            .group_by(Collection.id)
            .order_by(Collection.name.asc())
        )
        result = await self.db.execute(query)
        return list(result.all())

    async def update_collection(
        self, collection: Collection, update_data: dict
    ) -> Collection:
        """Update collection name or description."""
        for field, value in update_data.items():
            if hasattr(collection, field) and value is not None:
                setattr(collection, field, value)
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def delete_collection(self, collection: Collection) -> bool:
        """Delete collection record."""
        await self.db.delete(collection)
        await self.db.commit()
        return True

    async def is_video_in_collection(
        self, collection_id: UUID, user_video_id: UUID
    ) -> bool:
        """Check if video is already in collection."""
        query = select(CollectionVideo).where(
            CollectionVideo.collection_id == collection_id,
            CollectionVideo.user_video_id == user_video_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def add_video_to_collection(
        self, collection_id: UUID, user_video_id: UUID
    ) -> bool:
        """Add user video to collection."""
        if await self.is_video_in_collection(collection_id, user_video_id):
            return True

        cv = CollectionVideo(
            collection_id=collection_id,
            user_video_id=user_video_id,
        )
        self.db.add(cv)
        await self.db.commit()
        return True

    async def remove_video_from_collection(
        self, collection_id: UUID, user_video_id: UUID
    ) -> bool:
        """Remove user video from collection."""
        query = delete(CollectionVideo).where(
            CollectionVideo.collection_id == collection_id,
            CollectionVideo.user_video_id == user_video_id,
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
