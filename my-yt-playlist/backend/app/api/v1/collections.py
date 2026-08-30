from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionResponse,
    CollectionUpdateRequest,
)
from app.services.collection_service import CollectionService

router = APIRouter()


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom collection",
)
async def create_collection(
    data: CollectionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom playlist/collection."""
    service = CollectionService(db)
    return await service.create_collection(current_user.id, data)


@router.get(
    "",
    response_model=List[CollectionResponse],
    status_code=status.HTTP_200_OK,
    summary="List all user collections with video counts",
)
async def list_collections(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all collections owned by user with aggregated video counts."""
    service = CollectionService(db)
    return await service.list_collections(current_user.id)


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get collection details",
)
async def get_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single collection details by ID."""
    service = CollectionService(db)
    collection = await service.get_collection(current_user.id, collection_id)
    collections = await service.list_collections(current_user.id)
    target = next((c for c in collections if c.id == collection_id), None)
    return target or collection


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update collection name or description",
)
async def update_collection(
    collection_id: UUID,
    data: CollectionUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update collection name or description."""
    service = CollectionService(db)
    return await service.update_collection(current_user.id, collection_id, data)


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection",
)
async def delete_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete collection by ID with IDOR protection."""
    service = CollectionService(db)
    await service.delete_collection(current_user.id, collection_id)
    return None


@router.post(
    "/{collection_id}/videos/{user_video_id}",
    status_code=status.HTTP_200_OK,
    summary="Add video to collection",
)
async def add_video_to_collection(
    collection_id: UUID,
    user_video_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add saved video to custom collection with double IDOR protection."""
    service = CollectionService(db)
    await service.add_video_to_collection(current_user.id, collection_id, user_video_id)
    return {"message": "Video added to collection successfully."}


@router.delete(
    "/{collection_id}/videos/{user_video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove video from collection",
)
async def remove_video_from_collection(
    collection_id: UUID,
    user_video_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove video from collection with IDOR protection."""
    service = CollectionService(db)
    await service.remove_video_from_collection(
        current_user.id, collection_id, user_video_id
    )
    return None
