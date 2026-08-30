import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_video_crud_and_idor_protection(async_client: AsyncClient):
    # 1. Register User A
    user_a_email = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "User A"},
    )
    token_a = reg_a.json()["tokens"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_email = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "User B"},
    )
    token_b = reg_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A Adds Video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    add_res = await async_client.post(
        "/api/v1/videos",
        json={"url": video_url},
        headers=headers_a,
    )
    assert add_res.status_code == 201
    user_video_a = add_res.json()
    uv_id_a = user_video_a["id"]
    assert user_video_a["video"]["youtube_video_id"] == "dQw4w9WgXcQ"

    # 4. User A attempts Duplicate Add -> 409 Conflict
    dup_res = await async_client.post(
        "/api/v1/videos",
        json={"url": video_url},
        headers=headers_a,
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "DUPLICATE_RESOURCE"

    # 5. User A Reads Video Details
    get_res = await async_client.get(f"/api/v1/videos/{uv_id_a}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == uv_id_a

    # 6. User A Updates Video State
    patch_res = await async_client.patch(
        f"/api/v1/videos/{uv_id_a}",
        json={"status": "watched", "is_favourite": True, "notes": "Great video!"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["status"] == "watched"
    assert updated_data["is_favourite"] is True
    assert updated_data["watched_at"] is not None

    # 7. User A Adds Timestamp Note
    note_res = await async_client.post(
        f"/api/v1/videos/{uv_id_a}/notes",
        json={"timestamp_seconds": 120, "note_text": "Key takeaway at 2 minutes"},
        headers=headers_a,
    )
    assert note_res.status_code == 201
    note_id = note_res.json()["id"]

    # 8. IDOR TEST: User B tries to Read User A's Video -> 404 Not Found
    idor_read = await async_client.get(f"/api/v1/videos/{uv_id_a}", headers=headers_b)
    assert idor_read.status_code == 404

    # 9. IDOR TEST: User B tries to Update User A's Video -> 404 Not Found
    idor_patch = await async_client.patch(
        f"/api/v1/videos/{uv_id_a}",
        json={"notes": "Hacked notes"},
        headers=headers_b,
    )
    assert idor_patch.status_code == 404

    # 10. IDOR TEST: User B tries to Delete User A's Video -> 404 Not Found
    idor_delete = await async_client.delete(f"/api/v1/videos/{uv_id_a}", headers=headers_b)
    assert idor_delete.status_code == 404

    # 11. User A Deletes Timestamp Note
    del_note_res = await async_client.delete(
        f"/api/v1/videos/{uv_id_a}/notes/{note_id}",
        headers=headers_a,
    )
    assert del_note_res.status_code == 204

    # 12. User A Deletes Video
    del_res = await async_client.delete(f"/api/v1/videos/{uv_id_a}", headers=headers_a)
    assert del_res.status_code == 204
