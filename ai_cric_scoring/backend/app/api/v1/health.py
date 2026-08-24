from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse | JSONResponse:
    service = HealthService(session)
    db_ok, database = await service.check()
    payload = HealthResponse(
        status="ok" if db_ok else "error",
        service="cricket-intelligence-api",
        environment=settings.app_env,
        database=database,
    )
    if not db_ok:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
