from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_scoring_service
from app.models.user import User
from app.schemas.scoring import (
    LiveMatchState,
    ScoringEventListResponse,
    ScoringEventRequest,
    SelectPlayerRequest,
    StartMatchRequest,
    UndoRequest,
)
from app.services.scoring import ScoringService

router = APIRouter(prefix="/matches", tags=["scoring"])


@router.post("/{match_id}/start", response_model=LiveMatchState)
async def start_match(
    match_id: UUID,
    payload: StartMatchRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.start_match(match_id, user.id, payload)


@router.post("/{match_id}/innings/{innings_id}/start", response_model=LiveMatchState)
async def start_innings(
    match_id: UUID,
    innings_id: UUID,
    payload: StartMatchRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.start_innings(match_id, innings_id, user.id, payload)


@router.get("/{match_id}/live", response_model=LiveMatchState)
async def get_live(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.get_live(match_id, user.id)


@router.post("/{match_id}/scoring/events", response_model=LiveMatchState)
async def record_scoring_event(
    match_id: UUID,
    payload: ScoringEventRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.record_event(match_id, user.id, payload)


@router.post("/{match_id}/scoring/select-batter", response_model=LiveMatchState)
async def select_batter(
    match_id: UUID,
    payload: SelectPlayerRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.select_batter(match_id, user.id, payload)


@router.post("/{match_id}/scoring/select-bowler", response_model=LiveMatchState)
async def select_bowler(
    match_id: UUID,
    payload: SelectPlayerRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.select_bowler(match_id, user.id, payload)


@router.post("/{match_id}/scoring/undo", response_model=LiveMatchState)
async def undo_scoring(
    match_id: UUID,
    payload: UndoRequest,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> LiveMatchState:
    return await scoring.undo(match_id, user.id, payload)


@router.get("/{match_id}/scoring/events", response_model=ScoringEventListResponse)
async def list_scoring_events(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    scoring: Annotated[ScoringService, Depends(get_scoring_service)],
) -> ScoringEventListResponse:
    return await scoring.list_events(match_id, user.id)
