import uuid
import pytest
from httpx import AsyncClient
from app.integrations.youtube import YouTubeClient, YouTubeVideoMetadata


@pytest.mark.asyncio
async def test_collections_and_tags_lifecycle(
    async_client: AsyncClient, monkeypatch
):
    # 1. Register User A
    email_a = f"col_user_a_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Col User A"},
    )
    token_a = reg_a.json()["tokens"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    email_b = f"col_user_b_{uuid.uuid4().hex[:8]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123!", "full_name": "Col User B"},
    )
    token_b = reg_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Mock YouTube metadata fetch
    async def mock_fetch_metadata(self, video_id: str):
        return YouTubeVideoMetadata(
            youtube_video_id=video_id,
            youtube_url=f"https://www.youtube.com/watch?v={video_id}",
            title="FastAPI & PostgreSQL Deep Dive",
            description="Architecture tutorial",
            channel_name="Tech Channel",
            channel_id="ch_1",
            thumbnail_url="http://example.com/t.jpg",
            duration_seconds=1200,
            published_at=None,
            category_id=None,
        )

    monkeypatch.setattr(YouTubeClient, "fetch_video_metadata", mock_fetch_metadata)

    # 3. User A adds a video
    add_res = await async_client.post(
        "/api/v1/videos",
        json={"url": "https://www.youtube.com/watch?v=yt_col_test"},
        headers=headers_a,
    )
    assert add_res.status_code == 201
    uv_id_a = add_res.json()["id"]

    # 4. User A creates Collection "Python"
    col_res = await async_client.post(
        "/api/v1/collections",
        json={"name": "Python", "description": "Python talks and tutorials"},
        headers=headers_a,
    )
    assert col_res.status_code == 201
    col_id_a = col_res.json()["id"]

    # Duplicate collection name -> 409 Conflict
    dup_col = await async_client.post(
        "/api/v1/collections",
        json={"name": "Python"},
        headers=headers_a,
    )
    assert dup_col.status_code == 409

    # 5. User A creates Tag "fastapi"
    tag_res = await async_client.post(
        "/api/v1/tags",
        json={"name": "fastapi"},
        headers=headers_a,
    )
    assert tag_res.status_code == 201
    tag_id_a = tag_res.json()["id"]

    # Duplicate tag name -> 409 Conflict
    dup_tag = await async_client.post(
        "/api/v1/tags",
        json={"name": "fastapi"},
        headers=headers_a,
    )
    assert dup_tag.status_code == 409

    # 6. Add video to collection & attach tag
    add_to_col = await async_client.post(
        f"/api/v1/collections/{col_id_a}/videos/{uv_id_a}",
        headers=headers_a,
    )
    assert add_to_col.status_code == 200

    attach_tag = await async_client.post(
        f"/api/v1/tags/videos/{uv_id_a}/tags/{tag_id_a}",
        headers=headers_a,
    )
    assert attach_tag.status_code == 200

    # 7. List Collections & Tags (verify counts)
    cols_res = await async_client.get("/api/v1/collections", headers=headers_a)
    assert cols_res.status_code == 200
    assert cols_res.json()[0]["video_count"] == 1

    tags_res = await async_client.get("/api/v1/tags", headers=headers_a)
    assert tags_res.status_code == 200
    assert tags_res.json()[0]["usage_count"] == 1

    # 8. Query videos filtered by collection_id and tag_id
    filter_col = await async_client.get(
        f"/api/v1/videos?collection_id={col_id_a}", headers=headers_a
    )
    assert filter_col.status_code == 200
    assert len(filter_col.json()["items"]) == 1

    filter_tag = await async_client.get(
        f"/api/v1/videos?tag_id={tag_id_a}", headers=headers_a
    )
    assert filter_tag.status_code == 200
    assert len(filter_tag.json()["items"]) == 1

    # 9. IDOR TEST: User B tries to delete User A's collection -> 404 Not Found
    idor_col = await async_client.delete(
        f"/api/v1/collections/{col_id_a}", headers=headers_b
    )
    assert idor_col.status_code == 404

    # 10. IDOR TEST: User B tries to delete User A's tag -> 404 Not Found
    idor_tag = await async_client.delete(
        f"/api/v1/tags/{tag_id_a}", headers=headers_b
    )
    assert idor_tag.status_code == 404

    # 11. Remove video from collection & detach tag
    rem_col = await async_client.delete(
        f"/api/v1/collections/{col_id_a}/videos/{uv_id_a}",
        headers=headers_a,
    )
    assert rem_col.status_code == 204

    rem_tag = await async_client.delete(
        f"/api/v1/tags/videos/{uv_id_a}/tags/{tag_id_a}",
        headers=headers_a,
    )
    assert rem_tag.status_code == 204
