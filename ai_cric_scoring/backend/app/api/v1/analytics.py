from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.ai.services.historical_intelligence_service import HistoricalIntelligenceService
from app.core.dependencies import (
    get_current_user,
    get_historical_intelligence_service,
    get_historical_stats_service,
)
from app.models.enums import MatchFormat
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    HistoricalQueryRequest,
    HistoricalQueryResponse,
    LeaderboardMetric,
    LeaderboardResponse,
    PlayerAnalyticsResponse,
    PlayerCompareRequest,
    PlayerCompareResponse,
    TeamAnalyticsResponse,
    TeamCompareRequest,
    TeamCompareResponse,
)
from app.services.historical_stats import HistoricalStatsService, scope_from_in, scope_from_params

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _scope_params(
    date_from: datetime | None,
    date_to: datetime | None,
    format: MatchFormat | None,
    team_id: UUID | None,
    last_n: int | None,
):
    return scope_from_params(date_from=date_from, date_to=date_to, format=format, team_id=team_id, last_n=last_n)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def analytics_overview(
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    format: MatchFormat | None = None,
    team_id: UUID | None = None,
    last_n: Annotated[int | None, Query(ge=1, le=50)] = None,
) -> AnalyticsOverviewResponse:
    return await stats.overview(user.id, _scope_params(date_from, date_to, format, team_id, last_n))


@router.get("/players/{player_id}", response_model=PlayerAnalyticsResponse)
async def player_analytics(
    player_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    format: MatchFormat | None = None,
    team_id: UUID | None = None,
    last_n: Annotated[int | None, Query(ge=1, le=50)] = None,
) -> PlayerAnalyticsResponse:
    return await stats.player_stats(user.id, player_id, _scope_params(date_from, date_to, format, team_id, last_n))


@router.get("/teams/{team_id}", response_model=TeamAnalyticsResponse)
async def team_analytics(
    team_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    format: MatchFormat | None = None,
    last_n: Annotated[int | None, Query(ge=1, le=50)] = None,
) -> TeamAnalyticsResponse:
    return await stats.team_stats(user.id, team_id, _scope_params(date_from, date_to, format, None, last_n))


@router.get("/leaderboards", response_model=LeaderboardResponse)
async def analytics_leaderboards(
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
    metric: LeaderboardMetric = "runs",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    format: MatchFormat | None = None,
    team_id: UUID | None = None,
    last_n: Annotated[int | None, Query(ge=1, le=50)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeaderboardResponse:
    return await stats.leaderboards(
        user.id,
        metric=metric,
        scope=_scope_params(date_from, date_to, format, team_id, last_n),
        limit=limit,
        offset=offset,
    )


@router.post("/compare/players", response_model=PlayerCompareResponse)
async def compare_players(
    payload: PlayerCompareRequest,
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
) -> PlayerCompareResponse:
    return await stats.compare_players(
        user.id,
        payload.player_a_id,
        payload.player_b_id,
        scope_from_in(payload.scope),
    )


@router.post("/compare/teams", response_model=TeamCompareResponse)
async def compare_teams(
    payload: TeamCompareRequest,
    user: Annotated[User, Depends(get_current_user)],
    stats: Annotated[HistoricalStatsService, Depends(get_historical_stats_service)],
) -> TeamCompareResponse:
    return await stats.compare_teams(
        user.id,
        payload.team_a_id,
        payload.team_b_id,
        scope_from_in(payload.scope),
    )


@router.post("/query", response_model=HistoricalQueryResponse)
async def historical_query(
    payload: HistoricalQueryRequest,
    user: Annotated[User, Depends(get_current_user)],
    intelligence: Annotated[HistoricalIntelligenceService, Depends(get_historical_intelligence_service)],
) -> HistoricalQueryResponse:
    return await intelligence.query(user.id, payload.question.strip())
