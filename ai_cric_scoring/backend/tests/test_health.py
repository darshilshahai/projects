from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, get_db
from app.main import create_app


class _UnhealthySession:
    async def execute(self, _statement: object) -> None:
        raise ConnectionError("database unavailable")


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "cricket-intelligence-api"
    assert body["database"] == "connected"
    assert "environment" in body


@pytest.mark.asyncio
async def test_health_database_disconnected() -> None:
    app = create_app()

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield _UnhealthySession()  # type: ignore[misc]

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "disconnected"


@pytest.mark.asyncio
async def test_database_connectivity() -> None:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")
