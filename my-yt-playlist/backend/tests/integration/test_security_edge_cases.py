import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_presence(async_client: AsyncClient):
    res = await async_client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_unauthenticated_request_handling(async_client: AsyncClient):
    res = await async_client.get("/api/v1/users/me")
    assert res.status_code == 401
    assert "error" in res.json() or "detail" in res.json()


@pytest.mark.asyncio
async def test_invalid_jwt_token(async_client: AsyncClient):
    res = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer malformed.invalid.token"},
    )
    assert res.status_code == 401
    error = res.json()["error"]
    assert error["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_invalid_youtube_url_ingestion(async_client: AsyncClient):
    email = f"edge_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Edge Tester"},
    )
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    bad_url_res = await async_client.post(
        "/api/v1/videos",
        json={"url": "https://not-youtube.com/watch?v=12345"},
        headers=headers,
    )
    assert bad_url_res.status_code == 400
    error = bad_url_res.json()["error"]
    assert error["code"] == "INVALID_YOUTUBE_URL"


@pytest.mark.asyncio
async def test_non_existent_entity_lookup(async_client: AsyncClient):
    email = f"edge_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Edge Tester"},
    )
    token = reg_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = str(uuid.uuid4())
    res = await async_client.get(f"/api/v1/videos/{fake_id}", headers=headers)
    assert res.status_code == 404
    error = res.json()["error"]
    assert error["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_pydantic_validation_error_format(async_client: AsyncClient):
    res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "Password123!", "full_name": "Test"},
    )
    assert res.status_code == 422
    error = res.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "details" in error
