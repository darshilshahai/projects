from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_player_service
from app.models.enums import PlayerRole
from app.models.player import Player
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerListResponse, PlayerPublic, PlayerUpdate
from app.schemas.team import TeamSummary
from app.services.player import PlayerService

router = APIRouter(prefix="/players", tags=["players"])


async def _player_public(service: PlayerService, player: Player, *, include_teams: bool) -> PlayerPublic:
    teams: list[TeamSummary] = []
    if include_teams:
        teams = [TeamSummary.model_validate(team) for team in await service.list_active_teams(player.id)]
    return PlayerPublic(
        id=player.id,
        name=player.name,
        player_role=player.player_role,
        batting_style=player.batting_style,
        bowling_style=player.bowling_style,
        is_active=player.is_active,
        created_at=player.created_at,
        updated_at=player.updated_at,
        teams=teams,
    )


@router.get("", response_model=PlayerListResponse)
async def list_players(
    user: Annotated[User, Depends(get_current_user)],
    players: Annotated[PlayerService, Depends(get_player_service)],
    search: Annotated[str | None, Query()] = None,
    role: Annotated[PlayerRole | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PlayerListResponse:
    items, total = await players.list_owned(
        user.id,
        search=search,
        role=role,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return PlayerListResponse(
        items=[await _player_public(players, player, include_teams=False) for player in items],
        total=total,
    )


@router.post("", response_model=PlayerPublic, status_code=status.HTTP_201_CREATED)
async def create_player(
    payload: PlayerCreate,
    user: Annotated[User, Depends(get_current_user)],
    players: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerPublic:
    player = await players.create(
        owner_user_id=user.id,
        name=payload.name,
        player_role=payload.player_role,
        batting_style=payload.batting_style,
        bowling_style=payload.bowling_style,
    )
    return await _player_public(players, player, include_teams=False)


@router.get("/{player_id}", response_model=PlayerPublic)
async def get_player(
    player_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    players: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerPublic:
    player = await players.get_owned(player_id, user.id)
    return await _player_public(players, player, include_teams=True)


@router.patch("/{player_id}", response_model=PlayerPublic)
async def update_player(
    player_id: UUID,
    payload: PlayerUpdate,
    user: Annotated[User, Depends(get_current_user)],
    players: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerPublic:
    player = await players.update_owned(
        player_id,
        user.id,
        name=payload.name,
        player_role=payload.player_role,
        batting_style=payload.batting_style,
        bowling_style=payload.bowling_style,
        is_active=payload.is_active,
    )
    return await _player_public(players, player, include_teams=True)
