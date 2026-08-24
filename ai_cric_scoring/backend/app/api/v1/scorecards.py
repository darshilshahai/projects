from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_scorecard_service
from app.models.user import User
from app.schemas.scorecard import MatchScorecardResponse
from app.services.scorecard import ScorecardService

router = APIRouter(prefix="/matches", tags=["scorecard"])


@router.get("/{match_id}/scorecard", response_model=MatchScorecardResponse)
async def get_match_scorecard(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    scorecard: Annotated[ScorecardService, Depends(get_scorecard_service)],
) -> MatchScorecardResponse:
    return await scorecard.get_match_scorecard(match_id, user.id)
