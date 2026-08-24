from __future__ import annotations

import uuid

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.analytics.history.definitions import DISMISSAL_STATUSES
from app.analytics.history.filters import HistoricalScope
from app.analytics.history.rankings import RankingCandidate
from app.analytics.history.types import (
    AppearanceRow,
    BattingInningsRow,
    BowlingInningsRow,
    TeamMatchRow,
)
from app.models.enums import MatchStatus, ResultType
from app.models.innings import Innings
from app.models.innings_stats import InningsBattingStat, InningsBowlingStat
from app.models.match import Match
from app.models.match_player import MatchPlayer
from app.models.match_team import MatchTeam
from app.models.player import Player
from app.models.score_snapshot import ScoreSnapshot
from app.models.team import Team


class HistoricalStatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def player_owned(self, player_id: uuid.UUID, user_id: uuid.UUID) -> Player | None:
        stmt = select(Player).where(Player.id == player_id, Player.owner_user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def team_owned(self, team_id: uuid.UUID, user_id: uuid.UUID) -> Team | None:
        stmt = select(Team).where(Team.id == team_id, Team.owner_user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_owned_players(self, user_id: uuid.UUID) -> list[Player]:
        stmt = select(Player).where(Player.owner_user_id == user_id).order_by(Player.name.asc())
        return list((await self._session.execute(stmt)).scalars())

    async def list_owned_teams(self, user_id: uuid.UUID) -> list[Team]:
        stmt = select(Team).where(Team.owner_user_id == user_id).order_by(Team.name.asc())
        return list((await self._session.execute(stmt)).scalars())

    async def completed_match_count(self, user_id: uuid.UUID, scope: HistoricalScope) -> int:
        if scope.last_n is not None:
            return len(await self._recent_match_ids(user_id, scope))
        stmt = select(func.count(Match.id)).select_from(Match)
        stmt = self._apply_match_scope(stmt, user_id, scope)
        if scope.team_id is not None:
            stmt = stmt.where(Match.id.in_(select(MatchTeam.match_id).where(MatchTeam.team_id == scope.team_id)))
        return int(await self._session.scalar(stmt) or 0)

    async def player_appearances(
        self,
        user_id: uuid.UUID,
        player_id: uuid.UUID,
        scope: HistoricalScope,
    ) -> list[AppearanceRow]:
        own = aliased(MatchTeam)
        opp = aliased(MatchTeam)
        stmt = (
            select(
                MatchPlayer.match_id,
                MatchPlayer.player_id,
                own.team_id,
                Match.completed_at,
                Match.format,
                Match.balls_per_over,
                opp.team_name_snapshot,
                Match.result_type,
                Match.winner_match_team_id,
                MatchPlayer.match_team_id,
                MatchPlayer.display_name_snapshot,
            )
            .select_from(MatchPlayer)
            .join(Match, Match.id == MatchPlayer.match_id)
            .join(own, own.id == MatchPlayer.match_team_id)
            .join(opp, and_(opp.match_id == Match.id, opp.id != own.id))
            .where(MatchPlayer.player_id == player_id, MatchPlayer.is_playing.is_(True))
        )
        stmt = self._apply_match_scope(stmt, user_id, scope, team_column=own.team_id)
        stmt = stmt.order_by(Match.completed_at.desc().nulls_last(), Match.id.desc())
        rows = (await self._session.execute(stmt)).all()
        appearances = [
            AppearanceRow(
                match_id=row.match_id,
                player_id=row.player_id,
                team_id=row.team_id,
                completed_at=row.completed_at,
                format=row.format.value if hasattr(row.format, "value") else str(row.format),
                balls_per_over=row.balls_per_over,
                opponent_name=row.team_name_snapshot,
                result_code=_result_code(row.result_type, row.winner_match_team_id, row.match_team_id),
                display_name_snapshot=row.display_name_snapshot,
            )
            for row in rows
        ]
        return _apply_last_n(appearances, scope.last_n)

    async def batting_rows(
        self,
        user_id: uuid.UUID,
        player_id: uuid.UUID,
        match_ids: list[uuid.UUID],
    ) -> list[BattingInningsRow]:
        if not match_ids:
            return []
        own = aliased(MatchTeam)
        opp = aliased(MatchTeam)
        stmt = (
            select(
                Match.id.label("match_id"),
                MatchPlayer.player_id,
                InningsBattingStat.runs,
                InningsBattingStat.balls_faced,
                InningsBattingStat.fours,
                InningsBattingStat.sixes,
                InningsBattingStat.status,
                Match.completed_at,
                opp.team_name_snapshot,
                Match.result_type,
                Match.winner_match_team_id,
                MatchPlayer.match_team_id,
            )
            .select_from(InningsBattingStat)
            .join(MatchPlayer, MatchPlayer.id == InningsBattingStat.player_id)
            .join(Innings, Innings.id == InningsBattingStat.innings_id)
            .join(Match, Match.id == Innings.match_id)
            .join(own, own.id == MatchPlayer.match_team_id)
            .join(opp, and_(opp.match_id == Match.id, opp.id != own.id))
            .where(
                Match.created_by_user_id == user_id,
                Match.status == MatchStatus.COMPLETED,
                MatchPlayer.player_id == player_id,
                Match.id.in_(match_ids),
            )
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            BattingInningsRow(
                match_id=row.match_id,
                player_id=row.player_id,
                runs=row.runs,
                balls_faced=row.balls_faced,
                fours=row.fours,
                sixes=row.sixes,
                status=row.status,
                completed_at=row.completed_at,
                opponent_name=row.team_name_snapshot,
                result_code=_result_code(row.result_type, row.winner_match_team_id, row.match_team_id),
            )
            for row in rows
        ]

    async def bowling_rows(
        self,
        user_id: uuid.UUID,
        player_id: uuid.UUID,
        match_ids: list[uuid.UUID],
    ) -> list[BowlingInningsRow]:
        if not match_ids:
            return []
        own = aliased(MatchTeam)
        opp = aliased(MatchTeam)
        stmt = (
            select(
                Match.id.label("match_id"),
                MatchPlayer.player_id,
                InningsBowlingStat.legal_balls,
                InningsBowlingStat.runs_conceded,
                InningsBowlingStat.wickets,
                InningsBowlingStat.wides,
                InningsBowlingStat.no_balls,
                InningsBowlingStat.maidens,
                Match.balls_per_over,
                Match.completed_at,
                opp.team_name_snapshot,
                Match.result_type,
                Match.winner_match_team_id,
                MatchPlayer.match_team_id,
            )
            .select_from(InningsBowlingStat)
            .join(MatchPlayer, MatchPlayer.id == InningsBowlingStat.player_id)
            .join(Innings, Innings.id == InningsBowlingStat.innings_id)
            .join(Match, Match.id == Innings.match_id)
            .join(own, own.id == MatchPlayer.match_team_id)
            .join(opp, and_(opp.match_id == Match.id, opp.id != own.id))
            .where(
                Match.created_by_user_id == user_id,
                Match.status == MatchStatus.COMPLETED,
                MatchPlayer.player_id == player_id,
                Match.id.in_(match_ids),
            )
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            BowlingInningsRow(
                match_id=row.match_id,
                player_id=row.player_id,
                legal_balls=row.legal_balls,
                runs_conceded=row.runs_conceded,
                wickets=row.wickets,
                wides=row.wides,
                no_balls=row.no_balls,
                maidens=row.maidens,
                balls_per_over=row.balls_per_over,
                completed_at=row.completed_at,
                opponent_name=row.team_name_snapshot,
                result_code=_result_code(row.result_type, row.winner_match_team_id, row.match_team_id),
            )
            for row in rows
        ]

    async def team_matches(
        self,
        user_id: uuid.UUID,
        team_id: uuid.UUID,
        scope: HistoricalScope,
    ) -> list[TeamMatchRow]:
        own = aliased(MatchTeam)
        opp = aliased(MatchTeam)
        batting_innings = aliased(Innings)
        bowling_innings = aliased(Innings)
        batting_snap = aliased(ScoreSnapshot)
        bowling_snap = aliased(ScoreSnapshot)
        stmt = (
            select(
                Match.id.label("match_id"),
                own.team_id,
                own.id.label("match_team_id"),
                Match.completed_at,
                Match.format,
                Match.result_type,
                Match.winner_match_team_id,
                batting_innings.innings_number,
                batting_snap.total_runs,
                batting_snap.wickets,
                bowling_snap.total_runs.label("conceded"),
                opp.team_name_snapshot,
                opp.team_id.label("opponent_team_id"),
            )
            .select_from(own)
            .join(Match, Match.id == own.match_id)
            .join(opp, and_(opp.match_id == Match.id, opp.id != own.id))
            .outerjoin(batting_innings, batting_innings.batting_match_team_id == own.id)
            .outerjoin(batting_snap, batting_snap.innings_id == batting_innings.id)
            .outerjoin(bowling_innings, bowling_innings.bowling_match_team_id == own.id)
            .outerjoin(bowling_snap, bowling_snap.innings_id == bowling_innings.id)
            .where(own.team_id == team_id)
        )
        stmt = self._apply_match_scope(stmt, user_id, scope)
        stmt = stmt.order_by(Match.completed_at.desc().nulls_last(), Match.id.desc())
        rows = (await self._session.execute(stmt)).all()
        matches: dict[uuid.UUID, TeamMatchRow] = {}
        for row in rows:
            existing = matches.get(row.match_id)
            scored = row.total_runs if existing is None else existing.runs_scored or row.total_runs
            conceded = row.conceded if existing is None else existing.runs_conceded or row.conceded
            innings_number = (
                row.innings_number if existing is None else existing.batting_innings_number or row.innings_number
            )
            matches[row.match_id] = TeamMatchRow(
                match_id=row.match_id,
                team_id=row.team_id,
                match_team_id=row.match_team_id,
                completed_at=row.completed_at,
                format=row.format.value if hasattr(row.format, "value") else str(row.format),
                result_type=row.result_type.value if row.result_type is not None else None,
                winner_match_team_id=row.winner_match_team_id,
                batting_innings_number=innings_number,
                runs_scored=scored,
                wickets_lost=row.wickets if existing is None else existing.wickets_lost or row.wickets,
                runs_conceded=conceded,
                opponent_name=row.team_name_snapshot,
                opponent_team_id=row.opponent_team_id,
            )
        ordered = sorted(matches.values(), key=lambda item: item.completed_at or item.match_id, reverse=True)
        return _apply_last_n(ordered, scope.last_n)

    async def batting_leaderboard(self, user_id: uuid.UUID, scope: HistoricalScope) -> list[RankingCandidate]:
        stmt = (
            select(
                MatchPlayer.player_id,
                Player.name,
                func.sum(InningsBattingStat.runs).label("runs"),
                func.sum(InningsBattingStat.balls_faced).label("balls"),
                func.count(InningsBattingStat.id).label("innings"),
                func.sum(case((InningsBattingStat.status.in_(list(DISMISSAL_STATUSES)), 1), else_=0)).label(
                    "dismissals"
                ),
            )
            .select_from(InningsBattingStat)
            .join(MatchPlayer, MatchPlayer.id == InningsBattingStat.player_id)
            .join(Player, Player.id == MatchPlayer.player_id)
            .join(Innings, Innings.id == InningsBattingStat.innings_id)
            .join(Match, Match.id == Innings.match_id)
            .join(MatchTeam, MatchTeam.id == MatchPlayer.match_team_id)
            .where(Player.owner_user_id == user_id)
            .group_by(MatchPlayer.player_id, Player.name)
        )
        stmt = self._apply_match_scope(stmt, user_id, scope, team_column=MatchTeam.team_id)
        if scope.last_n:
            match_ids = await self._recent_match_ids(user_id, scope)
            if not match_ids:
                return []
            stmt = stmt.where(Match.id.in_(match_ids))
        rows = (await self._session.execute(stmt)).all()
        return [
            RankingCandidate(
                player_id=row.player_id,
                name=row.name,
                runs=int(row.runs or 0),
                balls=int(row.balls or 0),
                innings=int(row.innings or 0),
                dismissals=int(row.dismissals or 0),
            )
            for row in rows
        ]

    async def bowling_leaderboard(self, user_id: uuid.UUID, scope: HistoricalScope) -> list[RankingCandidate]:
        stmt = (
            select(
                MatchPlayer.player_id,
                Player.name,
                func.sum(InningsBowlingStat.wickets).label("wickets"),
                func.sum(InningsBowlingStat.runs_conceded).label("runs_conceded"),
                func.sum(InningsBowlingStat.legal_balls).label("legal_balls"),
                func.min(Match.balls_per_over).label("min_bpo"),
                func.max(Match.balls_per_over).label("max_bpo"),
            )
            .select_from(InningsBowlingStat)
            .join(MatchPlayer, MatchPlayer.id == InningsBowlingStat.player_id)
            .join(Player, Player.id == MatchPlayer.player_id)
            .join(Innings, Innings.id == InningsBowlingStat.innings_id)
            .join(Match, Match.id == Innings.match_id)
            .join(MatchTeam, MatchTeam.id == MatchPlayer.match_team_id)
            .where(Player.owner_user_id == user_id)
            .group_by(MatchPlayer.player_id, Player.name)
        )
        stmt = self._apply_match_scope(stmt, user_id, scope, team_column=MatchTeam.team_id)
        if scope.last_n:
            match_ids = await self._recent_match_ids(user_id, scope)
            if not match_ids:
                return []
            stmt = stmt.where(Match.id.in_(match_ids))
        rows = (await self._session.execute(stmt)).all()
        return [
            RankingCandidate(
                player_id=row.player_id,
                name=row.name,
                wickets=int(row.wickets or 0),
                runs_conceded=int(row.runs_conceded or 0),
                legal_balls=int(row.legal_balls or 0),
                balls_per_over=int(row.min_bpo) if row.min_bpo == row.max_bpo else None,
                mixed_rules=row.min_bpo != row.max_bpo,
            )
            for row in rows
        ]

    async def closing_phase_runs(
        self,
        user_id: uuid.UUID,
        team_id: uuid.UUID,
        match_ids: list[uuid.UUID],
    ) -> list[tuple[uuid.UUID, int, str, int, int]]:
        """Return (match_id, overs_per_innings, format, over_number, team_runs)."""
        if not match_ids:
            return []
        from app.models.delivery import Delivery

        stmt = (
            select(
                Match.id,
                Match.overs_per_innings,
                Match.format,
                Delivery.over_number,
                func.sum(
                    Delivery.runs_off_bat
                    + Delivery.wides
                    + Delivery.no_balls
                    + Delivery.byes
                    + Delivery.leg_byes
                    + Delivery.penalty_runs
                ).label("runs"),
            )
            .select_from(Delivery)
            .join(Innings, Innings.id == Delivery.innings_id)
            .join(Match, Match.id == Innings.match_id)
            .join(MatchTeam, MatchTeam.id == Innings.batting_match_team_id)
            .where(
                Match.created_by_user_id == user_id,
                Match.status == MatchStatus.COMPLETED,
                MatchTeam.team_id == team_id,
                Match.id.in_(match_ids),
                Delivery.is_voided.is_(False),
            )
            .group_by(Match.id, Match.overs_per_innings, Match.format, Delivery.over_number)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            (
                row[0],
                int(row[1] or 0),
                row[2].value if hasattr(row[2], "value") else str(row[2]),
                int(row[3]),
                int(row[4] or 0),
            )
            for row in rows
        ]

    def _apply_match_scope(
        self,
        stmt: Select,
        user_id: uuid.UUID,
        scope: HistoricalScope,
        *,
        team_column=None,
    ) -> Select:
        filters = [Match.created_by_user_id == user_id, Match.status == MatchStatus.COMPLETED]
        if scope.format is not None:
            filters.append(Match.format == scope.format)
        if scope.date_from is not None:
            filters.append(Match.completed_at >= scope.date_from)
        if scope.date_to is not None:
            filters.append(Match.completed_at <= scope.date_to)
        if scope.team_id is not None and team_column is not None:
            filters.append(team_column == scope.team_id)
        return stmt.where(*filters)

    async def _recent_match_ids(self, user_id: uuid.UUID, scope: HistoricalScope) -> list[uuid.UUID]:
        narrowed = scope.model_copy(update={"last_n": None})
        stmt = select(Match.id).select_from(Match)
        stmt = self._apply_match_scope(stmt, user_id, narrowed)
        if scope.team_id is not None:
            stmt = stmt.where(Match.id.in_(select(MatchTeam.match_id).where(MatchTeam.team_id == scope.team_id)))
        stmt = stmt.order_by(Match.completed_at.desc().nulls_last(), Match.id.desc())
        if scope.last_n:
            stmt = stmt.limit(scope.last_n)
        return list((await self._session.execute(stmt)).scalars())


def _apply_last_n[T](items: list[T], last_n: int | None) -> list[T]:
    if last_n is None:
        return items
    return items[:last_n]


def _result_code(
    result_type: ResultType | None,
    winner_match_team_id: uuid.UUID | None,
    own_match_team_id: uuid.UUID,
) -> str:
    if result_type is ResultType.TIED:
        return "T"
    if winner_match_team_id == own_match_team_id:
        return "W"
    return "L"
