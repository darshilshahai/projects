from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_current_user, get_roster_service, get_team_service
from app.models.team import Team
from app.models.team_player import TeamPlayer
from app.models.user import User
from app.schemas.roster import RosterAddRequest, RosterListResponse, RosterPlayerResponse
from app.schemas.team import TeamCreate, TeamListResponse, TeamPublic, TeamUpdate
from app.services.roster import RosterService
from app.services.team import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


def _team_public(team: Team, player_count: int) -> TeamPublic:
    return TeamPublic(
        id=team.id,
        name=team.name,
        short_name=team.short_name,
        is_active=team.is_active,
        player_count=player_count,
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


def _roster_item(membership: TeamPlayer) -> RosterPlayerResponse:
    player = membership.player
    return RosterPlayerResponse(
        membership_id=membership.id,
        player_id=player.id,
        name=player.name,
        player_role=player.player_role,
        batting_style=player.batting_style,
        bowling_style=player.bowling_style,
        is_active=membership.is_active,
        joined_at=membership.joined_at,
        left_at=membership.left_at,
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    user: Annotated[User, Depends(get_current_user)],
    teams: Annotated[TeamService, Depends(get_team_service)],
    search: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TeamListResponse:
    rows, total = await teams.list_owned(
        user.id,
        search=search,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return TeamListResponse(
        items=[_team_public(team, count) for team, count in rows],
        total=total,
    )


@router.post("", response_model=TeamPublic, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreate,
    user: Annotated[User, Depends(get_current_user)],
    teams: Annotated[TeamService, Depends(get_team_service)],
) -> TeamPublic:
    team = await teams.create(
        owner_user_id=user.id,
        name=payload.name,
        short_name=payload.short_name,
    )
    return _team_public(team, 0)


@router.get("/{team_id}", response_model=TeamPublic)
async def get_team(
    team_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    teams: Annotated[TeamService, Depends(get_team_service)],
) -> TeamPublic:
    team, count = await teams.get_owned(team_id, user.id)
    return _team_public(team, count)


@router.patch("/{team_id}", response_model=TeamPublic)
async def update_team(
    team_id: UUID,
    payload: TeamUpdate,
    user: Annotated[User, Depends(get_current_user)],
    teams: Annotated[TeamService, Depends(get_team_service)],
) -> TeamPublic:
    team, count = await teams.update_owned(
        team_id,
        user.id,
        name=payload.name,
        short_name=payload.short_name,
        is_active=payload.is_active,
        short_name_set="short_name" in payload.model_fields_set,
    )
    return _team_public(team, count)


@router.get("/{team_id}/players", response_model=RosterListResponse)
async def list_roster(
    team_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    roster: Annotated[RosterService, Depends(get_roster_service)],
    include_inactive: Annotated[bool, Query()] = False,
) -> RosterListResponse:
    items = await roster.list_roster(team_id, user.id, include_inactive=include_inactive)
    mapped = [_roster_item(item) for item in items]
    return RosterListResponse(items=mapped, total=len(mapped))


@router.post("/{team_id}/players", response_model=RosterPlayerResponse, status_code=status.HTTP_201_CREATED)
async def add_roster_player(
    team_id: UUID,
    payload: RosterAddRequest,
    user: Annotated[User, Depends(get_current_user)],
    roster: Annotated[RosterService, Depends(get_roster_service)],
) -> RosterPlayerResponse:
    membership = await roster.add_player(team_id, payload.player_id, user.id)
    return _roster_item(membership)


@router.delete("/{team_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_roster_player(
    team_id: UUID,
    player_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    roster: Annotated[RosterService, Depends(get_roster_service)],
) -> Response:
    await roster.remove_player(team_id, player_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
