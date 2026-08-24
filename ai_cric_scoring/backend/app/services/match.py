from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CaptainNotInXiError,
    DuplicatePlayingXiPlayerError,
    InactivePlayerError,
    InactiveTeamError,
    InvalidDateRangeError,
    InvalidMatchFormatError,
    InvalidOversError,
    InvalidPlayingXiSizeError,
    KeeperNotInXiError,
    MatchNotEditableError,
    MatchNotFoundError,
    MatchNotReadyError,
    PlayerNotInRosterError,
    ResourceNotFoundError,
    SameTeamSelectedError,
    TeamNotFoundError,
    TossTeamInvalidError,
)
from app.cricket.formatters import format_overs, format_result
from app.models.enums import MatchFormat, MatchSide, MatchStatus, TossDecision
from app.models.match import Match
from app.models.match_player import MatchPlayer
from app.models.match_team import MatchTeam
from app.models.player import Player
from app.models.team import Team
from app.repositories.match import MatchPlayerRepository, MatchRepository, MatchTeamRepository
from app.repositories.player import PlayerRepository
from app.repositories.team import TeamRepository
from app.repositories.team_player import TeamPlayerRepository
from app.schemas.match import (
    InningsSummaryPublic,
    MatchDetailResponse,
    MatchListScope,
    MatchPlayerPublic,
    MatchResultPublic,
    MatchSummary,
    MatchTeamPublic,
    PlayingXiPlayerRequest,
    PlayingXiTeamRequest,
    TeamScoreSummary,
    TossPublic,
)

FORMAT_OVERS: dict[MatchFormat, int] = {
    MatchFormat.T10: 10,
    MatchFormat.T20: 20,
    MatchFormat.ODI: 50,
}

IMMUTABLE_STATUSES = {
    MatchStatus.LIVE,
    MatchStatus.COMPLETED,
    MatchStatus.ABANDONED,
    MatchStatus.CANCELLED,
}

MIN_OVERS = 1
MAX_OVERS = 50
MIN_BALLS = 1
MAX_BALLS = 10
MIN_PLAYERS = 2
MAX_PLAYERS = 11


class MatchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._matches = MatchRepository(session)
        self._match_teams = MatchTeamRepository(session)
        self._match_players = MatchPlayerRepository(session)
        self._teams = TeamRepository(session)
        self._players = PlayerRepository(session)
        self._roster = TeamPlayerRepository(session)

    async def create_skeleton(
        self,
        *,
        created_by_user_id: uuid.UUID,
        team_a: Team,
        team_b: Team,
        match_format: MatchFormat,
        overs_per_innings: int,
        balls_per_over: int = 6,
        name: str | None = None,
        status: MatchStatus = MatchStatus.DRAFT,
        venue_name: str | None = None,
        players_per_team: int = 11,
    ) -> Match:
        match = Match(
            created_by_user_id=created_by_user_id,
            name=name or f"{team_a.name} vs {team_b.name}",
            format=match_format,
            status=status,
            venue_name=venue_name,
            overs_per_innings=overs_per_innings,
            balls_per_over=balls_per_over,
            players_per_team=players_per_team,
        )
        self._matches.add(match)
        await self._matches.flush()

        side_a = MatchTeam(
            match_id=match.id,
            team_id=team_a.id,
            team_name_snapshot=team_a.name,
            team_short_name_snapshot=team_a.short_name,
            side=MatchSide.TEAM_A,
        )
        side_b = MatchTeam(
            match_id=match.id,
            team_id=team_b.id,
            team_name_snapshot=team_b.name,
            team_short_name_snapshot=team_b.short_name,
            side=MatchSide.TEAM_B,
        )
        self._match_teams.add(side_a)
        self._match_teams.add(side_b)
        await self._match_teams.flush()
        return match

    async def add_player(
        self,
        *,
        match: Match,
        match_team: MatchTeam,
        player: Player,
        is_playing: bool = True,
        is_captain: bool = False,
        is_wicket_keeper: bool = False,
        batting_position: int | None = None,
    ) -> MatchPlayer:
        participant = MatchPlayer(
            match_id=match.id,
            match_team_id=match_team.id,
            player_id=player.id,
            display_name_snapshot=player.name,
            is_playing=is_playing,
            is_captain=is_captain,
            is_wicket_keeper=is_wicket_keeper,
            batting_position=batting_position,
        )
        self._match_players.add(participant)
        await self._match_players.flush()
        return participant

    async def get_with_participants(self, match_id: uuid.UUID) -> Match:
        match = await self._matches.get_with_participants(match_id)
        if match is None:
            raise ResourceNotFoundError("Match not found.")
        return match

    async def create_draft(
        self,
        *,
        user_id: uuid.UUID,
        match_format: MatchFormat,
        name: str | None = None,
        overs_per_innings: int | None = None,
        balls_per_over: int = 6,
        venue_name: str | None = None,
        scheduled_at: datetime | None = None,
        players_per_team: int = 11,
    ) -> Match:
        overs, balls, size = self._validated_settings(
            match_format,
            overs_per_innings=overs_per_innings,
            balls_per_over=balls_per_over,
            players_per_team=players_per_team,
        )
        match = Match(
            created_by_user_id=user_id,
            name=name,
            format=match_format,
            status=MatchStatus.DRAFT,
            venue_name=venue_name,
            scheduled_at=scheduled_at,
            overs_per_innings=overs,
            balls_per_over=balls,
            players_per_team=size,
        )
        self._matches.add(match)
        await self._matches.flush()
        await self._session.refresh(match)
        return match

    async def list_owned(
        self,
        user_id: uuid.UUID,
        *,
        status: MatchStatus | None = None,
        scope: MatchListScope | None = None,
        match_format: MatchFormat | None = None,
        team_id: uuid.UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Match], int]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise InvalidDateRangeError()
        return await self._matches.list_owned(
            user_id,
            status=status,
            scope=scope,
            match_format=match_format,
            team_id=team_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            limit=min(max(limit, 1), 100),
            offset=max(offset, 0),
        )

    async def list_summaries(
        self,
        user_id: uuid.UUID,
        *,
        status: MatchStatus | None = None,
        scope: MatchListScope | None = None,
        match_format: MatchFormat | None = None,
        team_id: uuid.UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MatchSummary], int]:
        items, total = await self.list_owned(
            user_id,
            status=status,
            scope=scope,
            match_format=match_format,
            team_id=team_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
        scores = await self._score_map(items)
        return [self.to_summary(item, scores.get(item.id, {})) for item in items], total

    async def get_owned_detail(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match:
        match = await self._matches.get_owned_with_participants(match_id, user_id)
        if match is None:
            raise MatchNotFoundError()
        return match

    async def update_draft(
        self,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        name: str | None = None,
        name_set: bool = False,
        match_format: MatchFormat | None = None,
        overs_per_innings: int | None = None,
        balls_per_over: int | None = None,
        venue_name: str | None = None,
        venue_set: bool = False,
        scheduled_at: datetime | None = None,
        scheduled_set: bool = False,
        players_per_team: int | None = None,
    ) -> Match:
        match = await self._editable_owned(match_id, user_id)
        if name_set:
            match.name = name
        if venue_set:
            match.venue_name = venue_name
        if scheduled_set:
            match.scheduled_at = scheduled_at
        next_format = match_format or match.format
        next_overs = overs_per_innings if overs_per_innings is not None else match.overs_per_innings
        next_balls = balls_per_over if balls_per_over is not None else match.balls_per_over
        next_size = players_per_team if players_per_team is not None else match.players_per_team
        if match_format is not None and match_format in FORMAT_OVERS:
            next_overs = FORMAT_OVERS[match_format]
        overs, balls, size = self._validated_settings(
            next_format,
            overs_per_innings=next_overs,
            balls_per_over=next_balls,
            players_per_team=next_size,
        )
        match.format = next_format
        match.overs_per_innings = overs
        match.balls_per_over = balls
        match.players_per_team = size
        await self._matches.flush()
        await self._session.refresh(match)
        return await self._after_config_change(match.id, user_id)

    async def set_teams(
        self,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        team_a_id: uuid.UUID,
        team_b_id: uuid.UUID,
    ) -> Match:
        if team_a_id == team_b_id:
            raise SameTeamSelectedError()
        match = await self._editable_owned_with_participants(match_id, user_id)
        team_a = await self._require_active_owned_team(team_a_id, user_id)
        team_b = await self._require_active_owned_team(team_b_id, user_id)

        existing = {item.side: item for item in match.match_teams}
        keep_xi: dict[MatchSide, list[MatchPlayer]] = {}
        if existing.get(MatchSide.TEAM_A) and existing[MatchSide.TEAM_A].team_id == team_a.id:
            keep_xi[MatchSide.TEAM_A] = list(existing[MatchSide.TEAM_A].match_players)
        if existing.get(MatchSide.TEAM_B) and existing[MatchSide.TEAM_B].team_id == team_b.id:
            keep_xi[MatchSide.TEAM_B] = list(existing[MatchSide.TEAM_B].match_players)

        match.toss_winner_match_team_id = None
        match.toss_decision = None
        await self._matches.flush()

        await self._match_players.delete_for_match(match.id)
        await self._match_teams.delete_for_match(match.id)
        await self._matches.flush()

        side_a = MatchTeam(
            match_id=match.id,
            team_id=team_a.id,
            team_name_snapshot=team_a.name,
            team_short_name_snapshot=team_a.short_name,
            side=MatchSide.TEAM_A,
        )
        side_b = MatchTeam(
            match_id=match.id,
            team_id=team_b.id,
            team_name_snapshot=team_b.name,
            team_short_name_snapshot=team_b.short_name,
            side=MatchSide.TEAM_B,
        )
        self._match_teams.add(side_a)
        self._match_teams.add(side_b)
        await self._matches.flush()

        for side, match_team in ((MatchSide.TEAM_A, side_a), (MatchSide.TEAM_B, side_b)):
            for previous in keep_xi.get(side, []):
                self._match_players.add(
                    MatchPlayer(
                        match_id=match.id,
                        match_team_id=match_team.id,
                        player_id=previous.player_id,
                        display_name_snapshot=previous.display_name_snapshot,
                        is_playing=previous.is_playing,
                        is_captain=previous.is_captain,
                        is_wicket_keeper=previous.is_wicket_keeper,
                        batting_position=previous.batting_position,
                    )
                )
        await self._matches.flush()
        return await self._after_config_change(match.id, user_id)

    async def set_playing_xi(
        self,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        teams: list[PlayingXiTeamRequest],
    ) -> Match:
        match = await self._editable_owned_with_participants(match_id, user_id)
        sides = {item.id: item for item in match.match_teams}
        selected_elsewhere = await self._match_players.list_player_ids_for_match(match.id)

        for payload in teams:
            match_team = sides.get(payload.match_team_id)
            if match_team is None:
                raise TeamNotFoundError()
            self._validate_xi_payload(payload.players, match.players_per_team)
            selected_elsewhere -= {player.player_id for player in match_team.match_players}
            await self._replace_side_xi(match, match_team, payload.players, selected_elsewhere, user_id)
            selected_elsewhere |= {item.player_id for item in payload.players}

        await self._matches.flush()
        return await self._after_config_change(match.id, user_id)

    async def set_toss(
        self,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        winner_match_team_id: uuid.UUID,
        decision: TossDecision,
    ) -> Match:
        match = await self._editable_owned_with_participants(match_id, user_id)
        if winner_match_team_id not in {item.id for item in match.match_teams}:
            raise TossTeamInvalidError()
        match.toss_winner_match_team_id = winner_match_team_id
        match.toss_decision = decision
        await self._matches.flush()
        await self._session.refresh(match)
        return await self._after_config_change(match.id, user_id)

    async def mark_ready(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match:
        match = await self._editable_owned_with_participants(match_id, user_id)
        issues = await self._readiness_issues(match)
        if issues:
            raise MatchNotReadyError(issues)
        match.status = MatchStatus.READY
        await self._matches.flush()
        await self._session.refresh(match)
        return await self.get_owned_detail(match.id, user_id)

    def to_summary(
        self,
        match: Match,
        scores: dict[uuid.UUID, TeamScoreSummary] | None = None,
    ) -> MatchSummary:
        by_side = {item.side: item for item in match.match_teams}
        team_a = by_side.get(MatchSide.TEAM_A)
        team_b = by_side.get(MatchSide.TEAM_B)
        score_map = scores or {}
        return MatchSummary(
            id=match.id,
            name=match.name,
            format=match.format,
            status=match.status,
            venue_name=match.venue_name,
            scheduled_at=match.scheduled_at,
            started_at=match.started_at,
            completed_at=match.completed_at,
            overs_per_innings=match.overs_per_innings,
            balls_per_over=match.balls_per_over,
            players_per_team=match.players_per_team,
            team_a_name=team_a.team_name_snapshot if team_a else None,
            team_b_name=team_b.team_name_snapshot if team_b else None,
            team_a_score=score_map.get(team_a.id) if team_a else None,
            team_b_score=score_map.get(team_b.id) if team_b else None,
            result=self._result_public(match),
            created_at=match.created_at,
            updated_at=match.updated_at,
        )

    async def to_detail(self, match: Match) -> MatchDetailResponse:
        issues = await self._readiness_issues(match)
        teams = [self._team_public(item) for item in sorted(match.match_teams, key=lambda row: row.side.value)]
        toss = None
        if match.toss_winner_match_team_id is not None and match.toss_decision is not None:
            toss = TossPublic(
                winner_match_team_id=match.toss_winner_match_team_id,
                decision=match.toss_decision,
            )
        return MatchDetailResponse(
            id=match.id,
            name=match.name,
            format=match.format,
            status=match.status,
            venue_name=match.venue_name,
            scheduled_at=match.scheduled_at,
            started_at=match.started_at,
            completed_at=match.completed_at,
            overs_per_innings=match.overs_per_innings,
            balls_per_over=match.balls_per_over,
            players_per_team=match.players_per_team,
            created_at=match.created_at,
            updated_at=match.updated_at,
            teams=teams,
            toss=toss,
            result=self._result_public(match),
            innings=await self._innings_summaries(match),
            readiness_issues=issues,
        )

    def _result_public(self, match: Match) -> MatchResultPublic | None:
        if match.result_type is None and match.winner_match_team_id is None:
            return None
        winner = next(
            (item for item in match.match_teams if item.id == match.winner_match_team_id),
            None,
        )
        winner_name = winner.team_name_snapshot if winner is not None else None
        return MatchResultPublic(
            result_type=match.result_type,
            winner_match_team_id=match.winner_match_team_id,
            winner_name=winner_name,
            margin_runs=match.margin_runs,
            margin_wickets=match.margin_wickets,
            summary=format_result(
                result_type=match.result_type,
                winner_name=winner_name,
                margin_runs=match.margin_runs,
                margin_wickets=match.margin_wickets,
            ),
        )

    async def _score_map(
        self,
        matches: list[Match],
    ) -> dict[uuid.UUID, dict[uuid.UUID, TeamScoreSummary]]:
        rows = await self._matches.list_score_rows([item.id for item in matches])
        by_id = {item.id: item for item in matches}
        result: dict[uuid.UUID, dict[uuid.UUID, TeamScoreSummary]] = {}
        for innings, snapshot in rows:
            match = by_id.get(innings.match_id)
            if match is None or snapshot is None:
                continue
            team = next(
                (item for item in match.match_teams if item.id == innings.batting_match_team_id),
                None,
            )
            if team is None:
                continue
            result.setdefault(match.id, {})[team.id] = TeamScoreSummary(
                match_team_id=team.id,
                name=team.team_name_snapshot,
                short_name=team.team_short_name_snapshot,
                runs=snapshot.total_runs,
                wickets=snapshot.wickets,
                legal_balls=snapshot.legal_balls,
                overs=format_overs(snapshot.legal_balls, match.balls_per_over),
                all_out=snapshot.wickets >= max(match.players_per_team - 1, 0),
            )
        return result

    async def _innings_summaries(self, match: Match) -> list[InningsSummaryPublic]:
        rows = await self._matches.list_score_rows([match.id])
        summaries: list[InningsSummaryPublic] = []
        for innings, snapshot in rows:
            if snapshot is None:
                continue
            team = next(
                (item for item in match.match_teams if item.id == innings.batting_match_team_id),
                None,
            )
            if team is None:
                continue
            summaries.append(
                InningsSummaryPublic(
                    number=innings.innings_number,
                    batting_match_team_id=team.id,
                    batting_team_name=team.team_name_snapshot,
                    runs=snapshot.total_runs,
                    wickets=snapshot.wickets,
                    legal_balls=snapshot.legal_balls,
                    overs=format_overs(snapshot.legal_balls, match.balls_per_over),
                    all_out=snapshot.wickets >= max(match.players_per_team - 1, 0),
                )
            )
        return summaries

    def _team_public(self, match_team: MatchTeam) -> MatchTeamPublic:
        players = sorted(
            match_team.match_players,
            key=lambda item: (item.batting_position is None, item.batting_position or 0, item.display_name_snapshot),
        )
        return MatchTeamPublic(
            id=match_team.id,
            team_id=match_team.team_id,
            side=match_team.side,
            name=match_team.team_name_snapshot,
            short_name=match_team.team_short_name_snapshot,
            players=[
                MatchPlayerPublic(
                    id=item.id,
                    player_id=item.player_id,
                    name=item.display_name_snapshot,
                    is_playing=item.is_playing,
                    is_captain=item.is_captain,
                    is_wicket_keeper=item.is_wicket_keeper,
                    batting_position=item.batting_position,
                    player_role=item.player.player_role if item.player else None,
                )
                for item in players
            ],
        )

    async def _replace_side_xi(
        self,
        match: Match,
        match_team: MatchTeam,
        players: list[PlayingXiPlayerRequest],
        occupied: set[uuid.UUID],
        user_id: uuid.UUID,
    ) -> None:
        seen: set[uuid.UUID] = set()
        captains = 0
        keepers = 0
        for item in players:
            if item.player_id in seen or item.player_id in occupied:
                raise DuplicatePlayingXiPlayerError()
            seen.add(item.player_id)
            if item.is_captain:
                captains += 1
            if item.is_wicket_keeper:
                keepers += 1
        if captains > 1:
            raise CaptainNotInXiError()
        if keepers > 1:
            raise KeeperNotInXiError()

        resolved: list[tuple[PlayingXiPlayerRequest, Player]] = []
        for item in players:
            player = await self._players.get_by_id_for_owner(item.player_id, user_id)
            if player is None:
                raise PlayerNotInRosterError()
            if not player.is_active:
                raise InactivePlayerError()
            membership = await self._roster.get_membership(match_team.team_id, player.id)
            if membership is None or not membership.is_active:
                raise PlayerNotInRosterError()
            resolved.append((item, player))

        await self._match_players.delete_for_match_team(match_team.id)
        for index, (item, player) in enumerate(resolved, start=1):
            self._match_players.add(
                MatchPlayer(
                    match_id=match.id,
                    match_team_id=match_team.id,
                    player_id=player.id,
                    display_name_snapshot=player.name,
                    is_playing=True,
                    is_captain=item.is_captain,
                    is_wicket_keeper=item.is_wicket_keeper,
                    batting_position=item.batting_position or index,
                )
            )

    def _validate_xi_payload(self, players: list[PlayingXiPlayerRequest], players_per_team: int) -> None:
        if len(players) > players_per_team:
            raise InvalidPlayingXiSizeError(f"Playing XI cannot exceed {players_per_team} players.")

    async def _require_active_owned_team(self, team_id: uuid.UUID, user_id: uuid.UUID) -> Team:
        team = await self._teams.get_by_id_for_owner(team_id, user_id)
        if team is None:
            raise TeamNotFoundError()
        if not team.is_active:
            raise InactiveTeamError()
        return team

    async def _editable_owned(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match:
        match = await self._matches.get_owned(match_id, user_id)
        if match is None:
            raise MatchNotFoundError()
        if match.status in IMMUTABLE_STATUSES:
            raise MatchNotEditableError()
        return match

    async def _editable_owned_with_participants(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match:
        match = await self.get_owned_detail(match_id, user_id)
        if match.status in IMMUTABLE_STATUSES:
            raise MatchNotEditableError()
        return match

    async def _after_config_change(self, match_id: uuid.UUID, user_id: uuid.UUID) -> Match:
        match = await self.get_owned_detail(match_id, user_id)
        if match.status is MatchStatus.READY:
            issues = await self._readiness_issues(match)
            if issues:
                match.status = MatchStatus.DRAFT
                await self._matches.flush()
                await self._session.refresh(match)
                match = await self.get_owned_detail(match_id, user_id)
        return match

    async def _readiness_issues(self, match: Match) -> list[str]:
        issues: list[str] = []
        by_side = {item.side: item for item in match.match_teams}
        team_a = by_side.get(MatchSide.TEAM_A)
        team_b = by_side.get(MatchSide.TEAM_B)
        if team_a is None or team_b is None:
            issues.append("Select two teams.")
            return issues
        if team_a.team_id == team_b.team_id:
            issues.append("Choose two different teams.")

        for label, match_team in (("Team A", team_a), ("Team B", team_b)):
            issues.extend(await self._side_readiness(label, match_team, match.players_per_team))

        if match.toss_winner_match_team_id is None or match.toss_decision is None:
            issues.append("Toss winner and decision are required.")
        elif match.toss_winner_match_team_id not in {team_a.id, team_b.id}:
            issues.append("Toss winner must be one of the match teams.")
        return issues

    async def _side_readiness(self, label: str, match_team: MatchTeam, players_per_team: int) -> list[str]:
        issues: list[str] = []
        playing = [item for item in match_team.match_players if item.is_playing]
        if len(playing) != players_per_team:
            issues.append(f"{label} Playing XI requires {players_per_team} players.")
        captains = [item for item in playing if item.is_captain]
        keepers = [item for item in playing if item.is_wicket_keeper]
        if len(captains) != 1:
            issues.append(f"{label} captain is not selected.")
        if len(keepers) != 1:
            issues.append(f"{label} wicketkeeper is not selected.")

        for item in playing:
            player = item.player
            if player is None or not player.is_active:
                issues.append(f"{label} includes an inactive player.")
                continue
            membership = await self._roster.get_membership(match_team.team_id, item.player_id)
            if membership is None or not membership.is_active:
                issues.append(f"{label} includes a player who is no longer on the roster.")
        return issues

    def _validated_settings(
        self,
        match_format: MatchFormat,
        *,
        overs_per_innings: int | None,
        balls_per_over: int,
        players_per_team: int,
    ) -> tuple[int, int, int]:
        if match_format is MatchFormat.TEST:
            raise InvalidMatchFormatError("Test matches are not supported yet.")
        if match_format in FORMAT_OVERS:
            overs = FORMAT_OVERS[match_format]
        else:
            if overs_per_innings is None:
                raise InvalidOversError("Custom matches require overs per innings.")
            overs = overs_per_innings
        if overs < MIN_OVERS or overs > MAX_OVERS:
            raise InvalidOversError()
        if balls_per_over < MIN_BALLS or balls_per_over > MAX_BALLS:
            raise InvalidOversError("Balls per over must be between 1 and 10.")
        if players_per_team < MIN_PLAYERS or players_per_team > MAX_PLAYERS:
            raise InvalidPlayingXiSizeError("Players per team must be between 2 and 11.")
        return overs, balls_per_over, players_per_team
