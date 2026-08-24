from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.ai.services.match_analysis_service import MatchAnalysisService
from app.core.dependencies import get_current_user, get_match_analysis_service
from app.models.user import User
from app.schemas.analysis import MatchAnalysisResponse

router = APIRouter(prefix="/matches", tags=["analysis"])


@router.get("/{match_id}/analysis", response_model=MatchAnalysisResponse)
async def get_match_analysis(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    analyses: Annotated[MatchAnalysisService, Depends(get_match_analysis_service)],
) -> MatchAnalysisResponse:
    return await analyses.get_analysis(match_id, user.id)


@router.post("/{match_id}/analysis", response_model=MatchAnalysisResponse)
async def generate_match_analysis(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    analyses: Annotated[MatchAnalysisService, Depends(get_match_analysis_service)],
) -> MatchAnalysisResponse:
    return await analyses.generate(match_id, user.id, regenerate=False)


@router.post("/{match_id}/analysis/regenerate", response_model=MatchAnalysisResponse)
async def regenerate_match_analysis(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    analyses: Annotated[MatchAnalysisService, Depends(get_match_analysis_service)],
) -> MatchAnalysisResponse:
    return await analyses.generate(match_id, user.id, regenerate=True)
