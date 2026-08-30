from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.tag import TagCreateRequest, TagResponse
from app.services.tag_service import TagService

router = APIRouter()


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reusable tag",
)
async def create_tag(
    data: TagCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new reusable tag for videos."""
    service = TagService(db)
    return await service.create_tag(current_user.id, data)


@router.get(
    "",
    response_model=List[TagResponse],
    status_code=status.HTTP_200_OK,
    summary="List all user tags with usage counts",
)
async def list_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all tags owned by user with aggregated video usage counts."""
    service = TagService(db)
    return await service.list_tags(current_user.id)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
)
async def delete_tag(
    tag_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete tag by ID with IDOR protection."""
    service = TagService(db)
    await service.delete_tag(current_user.id, tag_id)
    return None


@router.post(
    "/videos/{user_video_id}/tags/{tag_id}",
    status_code=status.HTTP_200_OK,
    summary="Attach tag to video",
)
async def attach_tag_to_video(
    user_video_id: UUID,
    tag_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach tag to video with double IDOR protection."""
    service = TagService(db)
    await service.attach_tag_to_video(current_user.id, user_video_id, tag_id)
    return {"message": "Tag attached to video successfully."}


@router.delete(
    "/videos/{user_video_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Detach tag from video",
)
async def detach_tag_from_video(
    user_video_id: UUID,
    tag_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Detach tag from video with IDOR protection."""
    service = TagService(db)
    await service.detach_tag_from_video(current_user.id, user_video_id, tag_id)
    return None
