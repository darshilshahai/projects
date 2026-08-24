from __future__ import annotations

import uuid

from app.analytics.history.batting import aggregate_batting
from app.analytics.history.bowling import aggregate_bowling
from app.analytics.history.comparisons import last_n_compare_note
from app.analytics.history.definitions import (
    MIN_DISMISSALS_FOR_AVERAGE_RANKING,
    MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING,
    RECENT_APPEARANCES,
    highest_score_display,
)
from app.analytics.history.filters import HistoricalScope
from app.analytics.history.form import batting_form_entries
from app.analytics.history.rankings import sort_leaderboard
from app.analytics.history.teams import aggregate_team, head_to_head
from app.core.exceptions import PlayerNotFoundError, TeamNotFoundError
from app.models.enums import MatchFormat
from app.models.player import Player
from app.models.team import Team
from app.repositories.historical_stats import HistoricalStatsRepository
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    BattingCareerOut,
    BowlingCareerOut,
    FormAppearanceOut,
    HeadToHeadOut,
    HistoricalScopeIn,
    HistoricalScopeOut,
    LeaderboardEntryOut,
    LeaderboardResponse,
    OverviewTeamForm,
    PlayerAnalyticsResponse,
    PlayerCompareResponse,
    TeamAnalyticsResponse,
    TeamCompareResponse,
)


def scope_from_params(
    *,
    date_from=None,
    date_to=None,
    format: MatchFormat | None = None,
    team_id: uuid.UUID | None = None,
    last_n: int | None = None,
) -> HistoricalScope:
    return HistoricalScope(
        date_from=date_from,
        date_to=date_to,
        format=format,
        team_id=team_id,
        last_n=last_n,
    ).normalized()


def scope_from_in(payload: HistoricalScopeIn) -> HistoricalScope:
    return HistoricalScope.model_validate(payload.model_dump()).normalized()


class HistoricalStatsService:
    def __init__(self, stats: HistoricalStatsRepository) -> None:
        self._stats = stats

    async def overview(self, user_id: uuid.UUID, scope: HistoricalScope) -> AnalyticsOverviewResponse:
        await self._ensure_scope(user_id, scope)
        completed = await self._stats.completed_match_count(user_id, scope)
        batting = sort_leaderboard("runs", await self._stats.batting_leaderboard(user_id, scope))
        bowling = sort_leaderboard("wickets", await self._stats.bowling_leaderboard(user_id, scope))
        teams = await self._stats.list_owned_teams(user_id)
        team_form = None
        best_matches = -1
        for team in teams:
            rows = await self._stats.team_matches(user_id, team.id, scope)
            career = aggregate_team(rows)
            if career.matches > best_matches:
                best_matches = career.matches
                team_form = OverviewTeamForm(
                    team_id=team.id,
                    name=team.name,
                    results=career.recent_results[:5],
                    win_percentage=career.win_percentage,
                    matches=career.matches,
                )
        players = await self._stats.list_owned_players(user_id)
        suggestions = _overview_suggestions(completed, batting, bowling, team_form)
        return AnalyticsOverviewResponse(
            completed_matches=completed,
            player_count=len(players),
            team_count=len(teams),
            top_runs=_entry("runs", batting[0]) if batting else None,
            top_wickets=_entry("wickets", bowling[0]) if bowling else None,
            team_form=team_form if best_matches > 0 else None,
            suggestions=suggestions,
        )

    async def player_stats(
        self, user_id: uuid.UUID, player_id: uuid.UUID, scope: HistoricalScope
    ) -> PlayerAnalyticsResponse:
        await self._ensure_scope(user_id, scope)
        player = await self._require_player(player_id, user_id)
        return await self._player_payload(user_id, player, scope)

    async def team_stats(self, user_id: uuid.UUID, team_id: uuid.UUID, scope: HistoricalScope) -> TeamAnalyticsResponse:
        team = await self._require_team(team_id, user_id)
        return await self._team_payload(user_id, team, scope)

    async def leaderboards(
        self,
        user_id: uuid.UUID,
        *,
        metric: str,
        scope: HistoricalScope,
        limit: int,
        offset: int,
    ) -> LeaderboardResponse:
        await self._ensure_scope(user_id, scope)
        if metric in {"runs", "batting_average", "strike_rate"}:
            candidates = await self._stats.batting_leaderboard(user_id, scope)
        else:
            candidates = await self._stats.bowling_leaderboard(user_id, scope)
        ranked = sort_leaderboard(metric, candidates)
        page = ranked[offset : offset + limit]
        qualification = None
        if metric == "batting_average":
            qualification = f"Minimum {MIN_DISMISSALS_FOR_AVERAGE_RANKING} dismissals"
        if metric == "economy":
            qualification = f"Minimum {MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING} legal balls"
        items = [_entry(metric, pair, sample=True) for pair in page]
        return LeaderboardResponse(
            metric=metric,
            scope=_scope_out(scope, len(ranked)),
            items=items,
            total=len(ranked),
            limit=limit,
            offset=offset,
            qualification=qualification,
        )

    async def compare_players(
        self,
        user_id: uuid.UUID,
        player_a_id: uuid.UUID,
        player_b_id: uuid.UUID,
        scope: HistoricalScope,
    ) -> PlayerCompareResponse:
        left = await self.player_stats(user_id, player_a_id, scope)
        right = await self.player_stats(user_id, player_b_id, scope)
        return PlayerCompareResponse(
            scope=left.scope,
            player_a=left,
            player_b=right,
            note=last_n_compare_note(scope),
        )

    async def compare_teams(
        self,
        user_id: uuid.UUID,
        team_a_id: uuid.UUID,
        team_b_id: uuid.UUID,
        scope: HistoricalScope,
    ) -> TeamCompareResponse:
        left = await self.team_stats(user_id, team_a_id, scope)
        right = await self.team_stats(user_id, team_b_id, scope)
        rows = await self._stats.team_matches(user_id, team_a_id, scope)
        h2h = head_to_head(team_a_id, team_b_id, rows)
        return TeamCompareResponse(
            scope=left.scope,
            team_a=left,
            team_b=right,
            head_to_head=HeadToHeadOut(**h2h),
        )

    async def _player_payload(
        self, user_id: uuid.UUID, player: Player, scope: HistoricalScope
    ) -> PlayerAnalyticsResponse:
        appearances = await self._stats.player_appearances(user_id, player.id, scope)
        match_ids = [item.match_id for item in appearances]
        batting_rows = await self._stats.batting_rows(user_id, player.id, match_ids)
        bowling_rows = await self._stats.bowling_rows(user_id, player.id, match_ids)
        batting = aggregate_batting(batting_rows, matches_played=len(appearances))
        bowling = aggregate_bowling(bowling_rows, matches_played=len(appearances))
        form = [
            FormAppearanceOut.model_validate(item)
            for item in batting_form_entries(batting_rows, last_n=RECENT_APPEARANCES)
        ]
        return PlayerAnalyticsResponse(
            player_id=player.id,
            name=player.name,
            is_active=player.is_active,
            scope=_scope_out(scope, len(appearances)),
            batting=_batting_out(batting),
            bowling=_bowling_out(bowling),
            recent_form=form,
            small_sample=batting.innings < 3,
        )

    async def _team_payload(self, user_id: uuid.UUID, team: Team, scope: HistoricalScope) -> TeamAnalyticsResponse:
        rows = await self._stats.team_matches(user_id, team.id, scope)
        career = aggregate_team(rows)
        recent = [
            FormAppearanceOut(
                match_id=row.match_id,
                completed_at=row.completed_at,
                opponent_name=row.opponent_name,
                display=str(row.runs_scored) if row.runs_scored is not None else None,
                result="W"
                if row.winner_match_team_id == row.match_team_id
                else ("T" if row.result_type == "TIED" else "L"),
            )
            for row in rows[:5]
        ]
        return TeamAnalyticsResponse(
            team_id=team.id,
            name=team.name,
            is_active=team.is_active,
            scope=_scope_out(scope, career.matches),
            matches=career.matches,
            wins=career.wins,
            losses=career.losses,
            ties=career.ties,
            win_percentage=career.win_percentage,
            average_runs_scored=career.average_runs_scored,
            average_runs_conceded=career.average_runs_conceded,
            highest_score=career.highest_score,
            lowest_completed_score=career.lowest_completed_score,
            matches_chasing=career.matches_chasing,
            wins_chasing=career.wins_chasing,
            matches_defending=career.matches_defending,
            wins_defending=career.wins_defending,
            recent_form=career.recent_results[:5],
            recent_matches=recent,
            small_sample=career.matches < 3,
        )

    async def _ensure_scope(self, user_id: uuid.UUID, scope: HistoricalScope) -> None:
        if scope.team_id is not None:
            await self._require_team(scope.team_id, user_id)

    async def _require_player(self, player_id: uuid.UUID, user_id: uuid.UUID) -> Player:
        player = await self._stats.player_owned(player_id, user_id)
        if player is None:
            raise PlayerNotFoundError()
        return player

    async def _require_team(self, team_id: uuid.UUID, user_id: uuid.UUID) -> Team:
        team = await self._stats.team_owned(team_id, user_id)
        if team is None:
            raise TeamNotFoundError()
        return team


def _scope_out(scope: HistoricalScope, sample: int) -> HistoricalScopeOut:
    return HistoricalScopeOut(
        date_from=scope.date_from,
        date_to=scope.date_to,
        format=scope.format,
        team_id=scope.team_id,
        last_n=scope.last_n,
        completed_only=True,
        description=scope.describe(sample),
    )


def _batting_out(career) -> BattingCareerOut:
    return BattingCareerOut(
        matches=career.matches,
        innings=career.innings,
        runs=career.runs,
        balls=career.balls,
        not_outs=career.not_outs,
        dismissals=career.dismissals,
        highest_score=career.highest_score,
        highest_score_display=highest_score_display(career.highest_score, career.highest_not_out),
        fours=career.fours,
        sixes=career.sixes,
        strike_rate=career.strike_rate,
        batting_average=career.batting_average,
    )


def _bowling_out(career) -> BowlingCareerOut:
    return BowlingCareerOut(
        matches=career.matches,
        innings_bowled=career.innings_bowled,
        legal_balls=career.legal_balls,
        overs_display=career.overs_display,
        runs_conceded=career.runs_conceded,
        wickets=career.wickets,
        wides=career.wides,
        no_balls=career.no_balls,
        maidens=career.maidens,
        economy=career.economy,
        bowling_average=career.bowling_average,
        best_bowling=career.best_bowling,
        mixed_rules=career.mixed_rules,
        runs_per_legal_ball=career.runs_per_legal_ball,
    )


def _entry(metric: str, pair, *, sample: bool = False) -> LeaderboardEntryOut:
    candidate, value = pair
    label = None
    if sample:
        if metric in {"runs", "batting_average", "strike_rate"}:
            label = f"{candidate.innings} innings"
        else:
            label = f"{candidate.legal_balls} balls"
    return LeaderboardEntryOut(
        player_id=candidate.player_id,
        name=candidate.name,
        metric=metric,
        value=value,
        innings=candidate.innings or None,
        sample_label=label,
    )


def _overview_suggestions(completed: int, batting, bowling, team_form: OverviewTeamForm | None) -> list[str]:
    if completed == 0:
        return []
    items = ["Who has scored the most runs?", "Who has taken the most wickets?"]
    if batting and bowling and batting[0][0].player_id != bowling[0][0].player_id:
        items.append(f"Compare {batting[0][0].name} and {bowling[0][0].name}")
    if team_form and team_form.matches >= 5:
        items.append(f"How has {team_form.name}'s recent form changed?")
    else:
        items.append("What is the team's win rate?")
    items.append("Are we improving while chasing?")
    return items[:5]
