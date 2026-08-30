import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.collection import Collection
from app.models.tag import Tag
from app.models.user import User
from app.models.video import TimestampNote, UserVideo, Video


@pytest.mark.asyncio
async def test_create_user_and_video_lifecycle(get_db_session: AsyncSession):
    """
    Test creating a User, Video, UserVideo, Collection, Tag, and TimestampNote,
    verifying relationships and database persistence.
    """
    session = get_db_session

    # 1. Create User
    test_user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed_argon2_password_string",
        full_name="Test Architect",
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    assert test_user.id is not None
    assert test_user.is_active is True

    # 2. Create Global Video
    yt_id = f"yt_{uuid.uuid4().hex[:8]}"
    global_video = Video(
        youtube_video_id=yt_id,
        youtube_url=f"https://www.youtube.com/watch?v={yt_id}",
        title="FastAPI & PostgreSQL Deep Dive",
        channel_name="Tech Channel",
        channel_id="UC_123456",
        duration_seconds=1800,
    )
    session.add(global_video)
    await session.commit()
    await session.refresh(global_video)

    assert global_video.id is not None

    # 3. Create UserVideo
    user_video = UserVideo(
        user_id=test_user.id,
        video_id=global_video.id,
        status="unwatched",
        is_favourite=True,
        notes="Important architecture lesson",
    )
    session.add(user_video)
    await session.commit()
    await session.refresh(user_video)

    assert user_video.id is not None
    assert user_video.is_favourite is True

    # 4. Create TimestampNote
    note = TimestampNote(
        user_video_id=user_video.id,
        timestamp_seconds=420,
        note_text="Key takeaway on index design",
    )
    session.add(note)
    await session.commit()

    # 5. Create Collection and assign video
    collection = Collection(
        user_id=test_user.id,
        name="System Design",
        description="Architecture resources",
    )
    collection.user_videos.append(user_video)
    session.add(collection)
    await session.commit()

    # 6. Create Tag and assign video
    tag = Tag(user_id=test_user.id, name="python")
    tag.user_videos.append(user_video)
    session.add(tag)
    await session.commit()

    # Query back and verify relations
    query = select(UserVideo).where(UserVideo.id == user_video.id)
    result = await session.execute(query)
    retrieved_uv = result.scalar_one()

    assert retrieved_uv.user_id == test_user.id
    assert retrieved_uv.video_id == global_video.id
