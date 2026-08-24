from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_match_service
from app.models.enums import MatchFormat, MatchStatus
from app.models.user import User
from app.schemas.match import (
    MatchCreate,
    MatchDetailResponse,
    MatchListResponse,
    MatchListScope,
    MatchTeamsRequest,
    MatchUpdate,
    PlayingXiRequest,
    TossRequest,
)
from app.services.match import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
async def list_matches(
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
    status_filter: Annotated[MatchStatus | None, Query(alias="status")] = None,
    scope: Annotated[MatchListScope | None, Query()] = None,
    match_format: Annotated[MatchFormat | None, Query(alias="format")] = None,
    team_id: Annotated[UUID | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MatchListResponse:
    items, total = await matches.list_summaries(
        user.id,
        status=status_filter,
        scope=scope,
        match_format=match_format,
        team_id=team_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return MatchListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=MatchDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    payload: MatchCreate,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    created = await matches.create_draft(
        user_id=user.id,
        match_format=payload.format,
        name=payload.name,
        overs_per_innings=payload.overs_per_innings,
        balls_per_over=payload.balls_per_over,
        venue_name=payload.venue_name,
        scheduled_at=payload.scheduled_at,
        players_per_team=payload.players_per_team,
    )
    loaded = await matches.get_owned_detail(created.id, user.id)
    return await matches.to_detail(loaded)


@router.get("/{match_id}", response_model=MatchDetailResponse)
async def get_match(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.get_owned_detail(match_id, user.id)
    return await matches.to_detail(loaded)


@router.patch("/{match_id}", response_model=MatchDetailResponse)
async def update_match(
    match_id: UUID,
    payload: MatchUpdate,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.update_draft(
        match_id,
        user.id,
        name=payload.name,
        name_set="name" in payload.model_fields_set,
        match_format=payload.format,
        overs_per_innings=payload.overs_per_innings,
        balls_per_over=payload.balls_per_over,
        venue_name=payload.venue_name,
        venue_set="venue_name" in payload.model_fields_set,
        scheduled_at=payload.scheduled_at,
        scheduled_set="scheduled_at" in payload.model_fields_set,
        players_per_team=payload.players_per_team,
    )
    return await matches.to_detail(loaded)


@router.put("/{match_id}/teams", response_model=MatchDetailResponse)
async def set_match_teams(
    match_id: UUID,
    payload: MatchTeamsRequest,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.set_teams(
        match_id,
        user.id,
        team_a_id=payload.team_a_id,
        team_b_id=payload.team_b_id,
    )
    return await matches.to_detail(loaded)


@router.put("/{match_id}/playing-xi", response_model=MatchDetailResponse)
async def set_playing_xi(
    match_id: UUID,
    payload: PlayingXiRequest,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.set_playing_xi(match_id, user.id, payload.teams)
    return await matches.to_detail(loaded)


@router.put("/{match_id}/toss", response_model=MatchDetailResponse)
async def set_toss(
    match_id: UUID,
    payload: TossRequest,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.set_toss(
        match_id,
        user.id,
        winner_match_team_id=payload.winner_match_team_id,
        decision=payload.decision,
    )
    return await matches.to_detail(loaded)


@router.post("/{match_id}/ready", response_model=MatchDetailResponse)
async def mark_match_ready(
    match_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    matches: Annotated[MatchService, Depends(get_match_service)],
) -> MatchDetailResponse:
    loaded = await matches.mark_ready(match_id, user.id)
    return await matches.to_detail(loaded)
