from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_vector_store
from app.core.config import Settings, get_settings
from app.vectorstores.chroma_vector_store import ChromaVectorStore


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    """
    Health-check response.
    """

    status: str
    application: str
    version: str
    environment: str
    vector_store_records: int
    timestamp: datetime


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
def health_check(
    vector_store: ChromaVectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Check whether the API and vector store are available.
    """

    return HealthResponse(
        status="healthy",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        vector_store_records=vector_store.count(),
        timestamp=datetime.now(timezone.utc),
    )
