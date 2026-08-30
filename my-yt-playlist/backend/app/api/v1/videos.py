from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.video import (
    PaginatedUserVideoResponse,
    TimestampNoteCreateRequest,
    TimestampNoteResponse,
    UserVideoResponse,
    VideoCreateRequest,
    VideoUpdateRequest,
)
from app.services.video_service import VideoService

router = APIRouter()


@router.post(
    "",
    response_model=UserVideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a video to personal library by URL",
)
async def add_video(
    data: VideoCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a YouTube video by URL.
    Validates format, extracts ID, fetches metadata, and links to user library.
    """
    service = VideoService(db)
    user_video = await service.add_video(current_user.id, data)
    return user_video


@router.get(
    "",
    response_model=PaginatedUserVideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Query user video library with search, filters, sorting, and pagination",
)
async def list_videos(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "added_at",
        pattern="^(added_at|published_at|title|duration_seconds)$",
        description="Field to sort by",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    status_val: Optional[str] = Query(None, alias="status", description="Filter by status (unwatched, watching, watched)"),
    is_favourite: Optional[bool] = Query(None, description="Filter by favourite status"),
    is_watch_later: Optional[bool] = Query(None, description="Filter by watch later status"),
    user_category: Optional[str] = Query(None, description="Filter by custom category"),
    channel_name: Optional[str] = Query(None, description="Filter by channel name"),
    tag_id: Optional[UUID] = Query(None, description="Filter by tag ID"),
    collection_id: Optional[UUID] = Query(None, description="Filter by collection ID"),
    max_duration_seconds: Optional[int] = Query(None, ge=0, description="Max duration in seconds"),
    q: Optional[str] = Query(None, description="Search term across title, channel, description, and notes"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search and filter saved video library with full-text ILIKE search,
    multi-field sorting, and offset pagination.
    """
    service = VideoService(db)
    return await service.list_user_videos(
        user_id=current_user.id,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        status=status_val,
        is_favourite=is_favourite,
        is_watch_later=is_watch_later,
        user_category=user_category,
        channel_name=channel_name,
        tag_id=tag_id,
        collection_id=collection_id,
        max_duration_seconds=max_duration_seconds,
        search_query=q,
    )


@router.get(
    "/quick-queue",
    response_model=List[UserVideoResponse],
    status_code=status.HTTP_200_OK,
    summary="Unique Feature: Smart Duration Quick-Queue ('What to watch next?')",
)
async def get_quick_queue(
    max_duration_seconds: int = Query(900, ge=1, description="Available free time window in seconds (default 900 = 15m)"),
    limit: int = Query(10, ge=1, le=50, description="Max candidate videos to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Unique V1 Feature: Smart Duration Quick-Queue.
    Returns unwatched videos fitting max_duration_seconds, prioritized by watch-later & favourite flags.
    """
    service = VideoService(db)
    items = await service.get_quick_queue(
        user_id=current_user.id,
        max_duration_seconds=max_duration_seconds,
        limit=limit,
    )
    return items


@router.get(
    "/{user_video_id}",
    response_model=UserVideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved video details",
)
async def get_video_details(
    user_video_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch single saved video details by ID with IDOR protection."""
    service = VideoService(db)
    user_video = await service.get_video_details(current_user.id, user_video_id)
    return user_video


@router.patch(
    "/{user_video_id}",
    response_model=UserVideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update saved video status, notes, or flags",
)
async def update_video(
    user_video_id: UUID,
    data: VideoUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update saved video user state (status, notes, favorite, watch-later)."""
    service = VideoService(db)
    updated = await service.update_video(current_user.id, user_video_id, data)
    return updated


@router.delete(
    "/{user_video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove video from library",
)
async def delete_video(
    user_video_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove video from user library with IDOR validation."""
    service = VideoService(db)
    await service.delete_video(current_user.id, user_video_id)
    return None


@router.post(
    "/{user_video_id}/notes",
    response_model=TimestampNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add timestamped note to saved video",
)
async def add_timestamp_note(
    user_video_id: UUID,
    data: TimestampNoteCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach structured time-linked note to video."""
    service = VideoService(db)
    note = await service.add_timestamp_note(current_user.id, user_video_id, data)
    return note


@router.delete(
    "/{user_video_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete timestamped note",
)
async def delete_timestamp_note(
    user_video_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete timestamped note from saved video."""
    service = VideoService(db)
    await service.delete_timestamp_note(current_user.id, user_video_id, note_id)
    return None
