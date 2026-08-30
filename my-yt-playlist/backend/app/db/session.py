from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

# Create async engine with asyncpg driver
engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=(settings.ENVIRONMENT == "development"),
    future=True,
    pool_pre_ping=True,  # Test connection health before using pooled connections
    pool_size=10,
    max_overflow=20,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for yields async database sessions.
    Ensures sessions are closed cleanly after each HTTP request context.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
