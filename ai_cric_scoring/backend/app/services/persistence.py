from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError


async def flush_or_raise_conflict(
    session: AsyncSession,
    message: str,
    *,
    code: str = "CONFLICT",
) -> None:
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        raise ConflictError(message, code=code) from exc
