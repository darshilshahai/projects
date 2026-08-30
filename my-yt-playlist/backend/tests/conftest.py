import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Session-scoped test database engine using NullPool."""
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URI,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def get_db_session(test_engine):
    """
    Async database session fixture for ORM integration tests.
    Yields session and closes it cleanly.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        yield session
        await session.close()


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTP client fixture for API integration tests.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
