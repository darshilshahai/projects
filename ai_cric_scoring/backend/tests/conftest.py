from __future__ import annotations

import asyncio
import os
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import PlayerRole
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.services.player import PlayerService
from app.services.team import TeamService
from app.services.user import UserService

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class _HealthySession:
    async def execute(self, _statement: object) -> None:
        return None


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield _HealthySession()  # type: ignore[misc]

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


def _test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", Settings().test_database_url)


def _ensure_test_database(test_url: str) -> None:
    parsed = make_url(test_url)
    database_name = parsed.database
    if not database_name:
        pytest.skip("TEST_DATABASE_URL is missing a database name.")
    admin_url = parsed.set(database="cricket_db")

    async def _create() -> None:
        engine = create_async_engine(
            admin_url.render_as_string(hide_password=False),
            isolation_level="AUTOCOMMIT",
        )
        try:
            async with engine.connect() as connection:
                exists = await connection.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :name"),
                    {"name": database_name},
                )
                if exists.scalar() is None:
                    await connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        finally:
            await engine.dispose()

    try:
        asyncio.run(_create())
    except Exception as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")


def _upgrade_test_database(test_url: str) -> None:
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": test_url},
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not migrate the test database: {result.stderr}")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = _test_database_url()
    _ensure_test_database(url)
    _upgrade_test_database(url)
    return url


@pytest.fixture
async def db_session(test_database_url: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            if transaction.is_active:
                await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    return await UserService(db_session).create(
        email="owner@example.com",
        password_hash="not-a-real-hash",
        display_name="Owner",
    )


@pytest.fixture
async def team(db_session: AsyncSession, user: User) -> Team:
    return await TeamService(db_session).create(
        owner_user_id=user.id,
        name="Blue XI",
        short_name="BLU",
    )


@pytest.fixture
async def player(db_session: AsyncSession, user: User) -> Player:
    return await PlayerService(db_session).create(
        owner_user_id=user.id,
        name="Rohit Sharma",
        player_role=PlayerRole.BATTER,
    )
