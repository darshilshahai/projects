import uuid
import pytest
from httpx import AsyncClient
from app.integrations.youtube import YouTubeClient, YouTubeVideoMetadata


@pytest.mark.asyncio
async def test_search_filtering_pagination_and_quick_queue(
    async_client: AsyncClient, monkeypatch
):
    # 1. Register test user
    email = f"search_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Search Tester"},
    )
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Mock YouTube Client to return distinct videos deterministically (11-char IDs)
    mock_videos = {
        "yt_python_1": YouTubeVideoMetadata(
            youtube_video_id="yt_python_1",
            youtube_url="https://www.youtube.com/watch?v=yt_python_1",
            title="Python FastAPI Tutorial Deep Dive",
            description="Learn FastAPI backend development step by step",
            channel_name="Core Tech Channel",
            channel_id="ch_1",
            thumbnail_url="http://example.com/t1.jpg",
            duration_seconds=600,  # 10 mins
            published_at=None,
            category_id=None,
        ),
        "yt_system_2": YouTubeVideoMetadata(
            youtube_video_id="yt_system_2",
            youtube_url="https://www.youtube.com/watch?v=yt_system_2",
            title="System Design B-Tree Indexes",
            description="Deep dive into PostgreSQL indexing and performance",
            channel_name="Database Academy",
            channel_id="ch_2",
            thumbnail_url="http://example.com/t2.jpg",
            duration_seconds=2400,  # 40 mins
            published_at=None,
            category_id=None,
        ),
        "yt_shorts_3": YouTubeVideoMetadata(
            youtube_video_id="yt_shorts_3",
            youtube_url="https://www.youtube.com/watch?v=yt_shorts_3",
            title="Quick Python Tips in 30 Seconds",
            description="Short tutorial on list comprehensions",
            channel_name="Core Tech Channel",
            channel_id="ch_1",
            thumbnail_url="http://example.com/t3.jpg",
            duration_seconds=30,  # 30 secs
            published_at=None,
            category_id=None,
        ),
    }

    async def mock_fetch_metadata(self, video_id: str):
        if video_id in mock_videos:
            return mock_videos[video_id]
        raise Exception(f"Video '{video_id}' not found in mock dictionary")

    monkeypatch.setattr(YouTubeClient, "fetch_video_metadata", mock_fetch_metadata)

    # 2. Add 3 videos to user library
    uv1_res = await async_client.post(
        "/api/v1/videos",
        json={"url": "https://www.youtube.com/watch?v=yt_python_1"},
        headers=headers,
    )
    assert uv1_res.status_code == 201
    uv1_id = uv1_res.json()["id"]

    uv2_res = await async_client.post(
        "/api/v1/videos",
        json={"url": "https://www.youtube.com/watch?v=yt_system_2"},
        headers=headers,
    )
    assert uv2_res.status_code == 201
    uv2_id = uv2_res.json()["id"]

    uv3_res = await async_client.post(
        "/api/v1/videos",
        json={"url": "https://www.youtube.com/watch?v=yt_shorts_3"},
        headers=headers,
    )
    assert uv3_res.status_code == 201
    uv3_id = uv3_res.json()["id"]

    # Mark yt_python_1 as favourite & watch later
    await async_client.patch(
        f"/api/v1/videos/{uv1_id}",
        json={"is_favourite": True, "is_watch_later": True},
        headers=headers,
    )

    # 3. Test Pagination (page=1, size=2)
    pag_res = await async_client.get(
        "/api/v1/videos?page=1&size=2&sort_by=added_at&order=asc",
        headers=headers,
    )
    assert pag_res.status_code == 200
    pag_data = pag_res.json()
    assert len(pag_data["items"]) == 2
    assert pag_data["meta"]["total_items"] == 3
    assert pag_data["meta"]["total_pages"] == 2
    assert pag_data["meta"]["has_next"] is True

    # 4. Test Filtering (is_favourite=true)
    fav_res = await async_client.get(
        "/api/v1/videos?is_favourite=true",
        headers=headers,
    )
    assert fav_res.status_code == 200
    fav_data = fav_res.json()
    assert len(fav_data["items"]) == 1
    assert fav_data["items"][0]["id"] == uv1_id

    # 5. Test Full-Text Search (q="System Design")
    search_res = await async_client.get(
        "/api/v1/videos?q=System Design",
        headers=headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["items"]) == 1
    assert search_data["items"][0]["id"] == uv2_id

    # 6. Test Smart Duration Quick-Queue (max_duration_seconds=900 = 15 mins)
    # Should include yt_python_1 (10 mins) and yt_shorts_3 (30 secs), but EXCLUDE yt_system_2 (40 mins)
    qq_res = await async_client.get(
        "/api/v1/videos/quick-queue?max_duration_seconds=900",
        headers=headers,
    )
    assert qq_res.status_code == 200
    qq_items = qq_res.json()
    assert len(qq_items) == 2
    returned_ids = [item["id"] for item in qq_items]
    assert uv1_id in returned_ids
    assert uv3_id in returned_ids
    assert uv2_id not in returned_ids

    # Verify prioritization: yt_python_1 (is_watch_later=True) comes FIRST
    assert qq_items[0]["id"] == uv1_id
