from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check(self) -> tuple[bool, Literal["connected", "disconnected"]]:
        try:
            await self._session.execute(text("SELECT 1"))
        except Exception:
            logger.warning("database_unreachable")
            return False, "disconnected"
        return True, "connected"
