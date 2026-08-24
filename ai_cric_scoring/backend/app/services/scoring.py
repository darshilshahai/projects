from __future__ import annotations

import time
from typing import NoReturn
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppError,
    MatchNotFoundError,
    MatchNotLiveError,
    MatchNotReadyToStartError,
    NothingToUndoError,
    ScoreConflictError,
)
from app.core.logging import get_logger
from app.cricket.commands import (
    DeliveryCommand,
    DismissalCommand,
    RetireCommand,
    SelectBatterCommand,
    SelectBowlerCommand,
)
from app.cricket.engine import ScoringEngine, new_match_state
from app.cricket.events import DomainEvent
from app.cricket.exceptions import CricketEngineError
from app.cricket.formatters import (
    balls_remaining,
    economy,
    format_overs,
    required_run_rate,
    required_runs,
    run_rate,
    strike_rate,
)
from app.cricket.replay import ScoringReplay
from app.cricket.rules import MatchRules
from app.cricket.serialization import innings_from_dict, innings_to_dict
from app.cricket.state import BowlerState, InningsState, MatchState
from app.cricket.types import BatterStatus, InningsStatus, MatchPlayStatus, ScoringEventType
from app.models.delivery import Delivery
from app.models.dismissal import Dismissal
from app.models.enums import MatchStatus, TossDecision
from app.models.innings import Innings
from app.models.innings_stats import InningsBattingStat, InningsBowlingStat
from app.models.match import Match
from app.models.match_team import MatchTeam
from app.models.score_snapshot import ScoreSnapshot
from app.models.scoring_event import ScoringEvent
from app.repositories.match import MatchRepository
from app.repositories.scoring import (
    BattingStatsRepository,
    BowlingStatsRepository,
    DeliveryRepository,
    DismissalRepository,
    InningsRepository,
    ScoreSnapshotRepository,
    ScoringEventRepository,
    utcnow,
)
from app.schemas.scoring import (
    CurrentOverBall,
    DeliveryPayload,
    LiveBatterCard,
    LiveBatterOption,
    LiveBowlerCard,
    LiveBowlerOption,
    LiveInnings,
    LiveMatchState,
    LiveTeam,
    ScoringEventListResponse,
    ScoringEventPublic,
    ScoringEventRequest,
    SelectPlayerRequest,
    StartMatchRequest,
    UndoRequest,
)

logger = get_logger(__name__)

USER_EVENT_TYPES = {
    ScoringEventType.DELIVERY_RECORDED,
    ScoringEventType.BATTER_SELECTED,
    ScoringEventType.BOWLER_SELECTED,
    ScoringEventType.BATTER_RETIRED,
}

CONFLICT_CODES = {
    "BATTER_SELECTION_REQUIRED",
    "BOWLER_SELECTION_REQUIRED",
    "INNINGS_COMPLETE",
    "MATCH_COMPLETE",
    "INNINGS_NOT_LIVE",
}


class ScoringService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._matches = MatchRepository(session)
        self._innings = InningsRepository(session)
        self._events = ScoringEventRepository(session)
        self._deliveries = DeliveryRepository(session)
        self._dismissals = DismissalRepository(session)
        self._snapshots = ScoreSnapshotRepository(session)
        self._batting = BattingStatsRepository(session)
        self._bowling = BowlingStatsRepository(session)
        self._engine = ScoringEngine()
        self._replay = ScoringReplay(self._engine)

    async def start_match(self, match_id: UUID, user_id: UUID, payload: StartMatchRequest) -> LiveMatchState:
        start = time.perf_counter()
        match = await self._lock_owned(match_id, user_id)
        existing = await self._events.get_by_client_event_id(match.id, payload.client_event_id)
        if existing is not None:
            return await self._live_state(match, idempotent=True)
        if match.status is MatchStatus.LIVE:
            raise MatchNotReadyToStartError("This match has already started.")
        if match.status is not MatchStatus.READY:
            raise MatchNotReadyToStartError()
        if any(item.status is InningsStatus.LIVE for item in await self._innings.list_for_match(match.id)):
            raise MatchNotReadyToStartError("A live innings already exists.")

        batting_team, bowling_team = self._opening_sides(match)
        self._validate_openers(match, batting_team, bowling_team, payload)
        innings = Innings(
            match_id=match.id,
            innings_number=1,
            batting_match_team_id=batting_team.id,
            bowling_match_team_id=bowling_team.id,
            status=InningsStatus.LIVE,
            started_at=utcnow(),
        )
        self._innings.add(innings)
        await self._innings.flush()

        state = new_match_state(
            match_id=match.id,
            rules=self._rules(match),
            batting_first_team_id=batting_team.id,
            bowling_first_team_id=bowling_team.id,
        )
        try:
            result = self._engine.start_innings(
                state,
                innings_number=1,
                batting_team_id=batting_team.id,
                bowling_team_id=bowling_team.id,
                batting_player_ids=self._xi_ids(match, batting_team.id),
                bowling_player_ids=self._xi_ids(match, bowling_team.id),
                striker_id=payload.striker_id,
                non_striker_id=payload.non_striker_id,
                bowler_id=payload.bowler_id,
            )
        except CricketEngineError as exc:
            self._raise_engine(exc)

        match.status = MatchStatus.LIVE
        match.started_at = utcnow()
        snapshot = ScoreSnapshot(match_id=match.id, innings_id=innings.id, revision=0, state_json={})
        self._snapshots.add(snapshot)
        await self._snapshots.flush()
        await self._persist_result(
            match,
            innings,
            snapshot,
            result.state,
            result.events,
            user_id=user_id,
            client_event_id=payload.client_event_id,
            base_revision=0,
            delivery=None,
            legal_balls_before=0,
        )
        live = await self._live_state(match)
        self._log(
            "match_started",
            user_id=user_id,
            match_id=match.id,
            innings_id=innings.id,
            client_event_id=payload.client_event_id,
            revision_before=0,
            revision_after=live.revision,
            event_type="INNINGS_STARTED",
            duration_ms=self._ms(start),
        )
        return live

    async def start_innings(
        self,
        match_id: UUID,
        innings_id: UUID,
        user_id: UUID,
        payload: StartMatchRequest,
    ) -> LiveMatchState:
        start = time.perf_counter()
        match = await self._lock_owned(match_id, user_id)
        existing = await self._events.get_by_client_event_id(match.id, payload.client_event_id)
        if existing is not None:
            return await self._live_state(match, idempotent=True)
        if match.status is not MatchStatus.LIVE:
            raise MatchNotLiveError()
        innings = await self._innings.get_for_update(innings_id)
        if innings is None or innings.match_id != match.id:
            raise MatchNotFoundError()
        if innings.status is not InningsStatus.NOT_STARTED:
            raise AppError("INNINGS_NOT_LIVE", "This innings cannot be started.", status_code=409)

        batting_team = self._team(match, innings.batting_match_team_id)
        bowling_team = self._team(match, innings.bowling_match_team_id)
        self._validate_openers(match, batting_team, bowling_team, payload)
        domain = await self._domain_state(match)
        try:
            result = self._engine.start_innings(
                domain,
                innings_number=innings.innings_number,
                batting_team_id=innings.batting_match_team_id,
                bowling_team_id=innings.bowling_match_team_id,
                batting_player_ids=self._xi_ids(match, batting_team.id),
                bowling_player_ids=self._xi_ids(match, bowling_team.id),
                striker_id=payload.striker_id,
                non_striker_id=payload.non_striker_id,
                bowler_id=payload.bowler_id,
                target_runs=innings.target_runs,
            )
        except CricketEngineError as exc:
            self._raise_engine(exc)

        innings.status = InningsStatus.LIVE
        innings.started_at = utcnow()
        snapshot = ScoreSnapshot(match_id=match.id, innings_id=innings.id, revision=0, state_json={})
        self._snapshots.add(snapshot)
        await self._snapshots.flush()
        await self._persist_result(
            match,
            innings,
            snapshot,
            result.state,
            result.events,
            user_id=user_id,
            client_event_id=payload.client_event_id,
            base_revision=0,
            delivery=None,
            legal_balls_before=0,
        )
        live = await self._live_state(match)
        self._log(
            "innings_started",
            user_id=user_id,
            match_id=match.id,
            innings_id=innings.id,
            client_event_id=payload.client_event_id,
            revision_before=0,
            revision_after=live.revision,
            event_type="INNINGS_STARTED",
            duration_ms=self._ms(start),
        )
        return live

    async def get_live(self, match_id: UUID, user_id: UUID) -> LiveMatchState:
        match = await self._owned_detail(match_id, user_id)
        if match.status not in {MatchStatus.LIVE, MatchStatus.COMPLETED}:
            raise MatchNotLiveError()
        return await self._live_state(match)

    async def record_event(self, match_id: UUID, user_id: UUID, payload: ScoringEventRequest) -> LiveMatchState:
        start = time.perf_counter()
        match, innings, snapshot = await self._lock_live(match_id, user_id)
        duplicate = await self._duplicate_or_conflict(match, snapshot, payload.client_event_id, payload.base_revision)
        if duplicate is not None:
            return duplicate
        domain = await self._domain_state(match)
        try:
            if payload.type == "RETIRE":
                player_id = (payload.retire.player_id if payload.retire else None) or snapshot.striker_id
                if player_id is None:
                    raise AppError("INVALID_NEXT_BATTER", "A batter must be selected to retire.", status_code=400)
                hurt = True if payload.retire is None else payload.retire.hurt
                result = self._engine.retire(domain, RetireCommand(player_id, hurt=hurt))
                delivery = None
            else:
                if payload.delivery is None:
                    raise AppError("INVALID_DELIVERY", "A delivery payload is required.", status_code=400)
                command = self._delivery_command(payload.delivery, snapshot)
                result = self._engine.apply_delivery(domain, command)
                delivery = command
        except CricketEngineError as exc:
            self._raise_engine(exc)

        legal_before = snapshot.legal_balls
        await self._persist_result(
            match,
            innings,
            snapshot,
            result.state,
            result.events,
            user_id=user_id,
            client_event_id=payload.client_event_id,
            base_revision=payload.base_revision,
            delivery=delivery,
            legal_balls_before=legal_before,
        )
        live = await self._live_state(match)
        self._log(
            "scoring_event",
            user_id=user_id,
            match_id=match.id,
            innings_id=innings.id,
            client_event_id=payload.client_event_id,
            revision_before=payload.base_revision,
            revision_after=live.revision,
            event_type=payload.type,
            duration_ms=self._ms(start),
        )
        return live

    async def select_batter(self, match_id: UUID, user_id: UUID, payload: SelectPlayerRequest) -> LiveMatchState:
        return await self._select_player(match_id, user_id, payload, kind="batter")

    async def select_bowler(self, match_id: UUID, user_id: UUID, payload: SelectPlayerRequest) -> LiveMatchState:
        return await self._select_player(match_id, user_id, payload, kind="bowler")

    async def undo(self, match_id: UUID, user_id: UUID, payload: UndoRequest) -> LiveMatchState:
        start = time.perf_counter()
        match = await self._lock_owned(match_id, user_id)
        duplicate = await self._events.get_by_client_event_id(match.id, payload.client_event_id)
        if duplicate is not None:
            return await self._live_state(match, idempotent=True)
        innings = await self._undo_innings(match)
        snapshot = await self._snapshots.get_for_update(innings.id)
        if snapshot is None:
            raise NothingToUndoError()
        if payload.base_revision != snapshot.revision:
            raise ScoreConflictError(snapshot.revision)

        events = await self._events.list_for_innings(innings.id)
        target = next(
            (item for item in reversed(events) if not item.is_voided and item.event_type in USER_EVENT_TYPES),
            None,
        )
        if target is None:
            raise NothingToUndoError()

        void_event = DomainEvent(
            ScoringEventType.DELIVERY_VOIDED,
            {"target_sequence": target.sequence_number},
        )
        await self._append_events(
            match,
            innings,
            [void_event],
            user_id=user_id,
            client_event_id=payload.client_event_id,
            base_revision=payload.base_revision,
        )
        target.is_voided = True
        delivery = await self._deliveries.get_by_event_id(target.id)
        if delivery is not None:
            delivery.is_voided = True

        rebuilt = self._replay.replay(
            [self._to_domain_event(item) for item in await self._events.list_for_innings(innings.id)],
            initial=await self._initial_state_for_innings(match, innings),
        )
        current = rebuilt.current_innings
        if current is None:
            raise NothingToUndoError()
        snapshot.revision = payload.base_revision + 1
        self._fill_snapshot(snapshot, current)
        await self._replace_stats(innings.id, current)
        innings.status = current.status
        innings.completed_at = utcnow() if current.status is InningsStatus.COMPLETED else None
        innings.target_runs = current.target_runs
        if current.status is InningsStatus.LIVE:
            await self._drop_unstarted_later_innings(match, innings.innings_number)
            if match.status is MatchStatus.COMPLETED:
                match.status = MatchStatus.LIVE
                match.completed_at = None
                match.result_type = None
                match.winner_match_team_id = None
                match.margin_runs = None
                match.margin_wickets = None
        self._apply_match_result(match, rebuilt)
        await self._session.flush()
        live = await self._live_state(match)
        self._log(
            "scoring_undo",
            user_id=user_id,
            match_id=match.id,
            innings_id=innings.id,
            client_event_id=payload.client_event_id,
            revision_before=payload.base_revision,
            revision_after=live.revision,
            event_type="DELIVERY_VOIDED",
            duration_ms=self._ms(start),
        )
        return live

    async def list_events(self, match_id: UUID, user_id: UUID) -> ScoringEventListResponse:
        match = await self._owned_detail(match_id, user_id)
        innings_rows = await self._innings.list_for_match(match.id)
        items: list[ScoringEventPublic] = []
        revision = 0
        for innings in innings_rows:
            snapshot = await self._snapshots.get_for_innings(innings.id)
            if snapshot is not None:
                revision = snapshot.revision
            for event in await self._events.list_for_innings(innings.id):
                items.append(
                    ScoringEventPublic(
                        id=event.id,
                        sequence_number=event.sequence_number,
                        event_type=event.event_type.value,
                        client_event_id=event.client_event_id,
                        is_voided=event.is_voided,
                        payload=event.payload,
                        created_by_user_id=event.created_by_user_id,
                        created_at=event.created_at.isoformat(),
                    )
                )
        return ScoringEventListResponse(items=items, revision=revision)

    async def _select_player(
        self,
        match_id: UUID,
        user_id: UUID,
        payload: SelectPlayerRequest,
        *,
        kind: str,
    ) -> LiveMatchState:
        start = time.perf_counter()
        match, innings, snapshot = await self._lock_live(match_id, user_id)
        duplicate = await self._duplicate_or_conflict(match, snapshot, payload.client_event_id, payload.base_revision)
        if duplicate is not None:
            return duplicate
        domain = await self._domain_state(match)
        try:
            if kind == "batter":
                result = self._engine.select_batter(domain, SelectBatterCommand(payload.player_id))
            else:
                result = self._engine.select_bowler(domain, SelectBowlerCommand(payload.player_id))
        except CricketEngineError as exc:
            self._raise_engine(exc)
        await self._persist_result(
            match,
            innings,
            snapshot,
            result.state,
            result.events,
            user_id=user_id,
            client_event_id=payload.client_event_id,
            base_revision=payload.base_revision,
            delivery=None,
            legal_balls_before=snapshot.legal_balls,
        )
        live = await self._live_state(match)
        self._log(
            "player_selected",
            user_id=user_id,
            match_id=match.id,
            innings_id=innings.id,
            client_event_id=payload.client_event_id,
            revision_before=payload.base_revision,
            revision_after=live.revision,
            event_type=kind.upper() + "_SELECTED",
            duration_ms=self._ms(start),
        )
        return live

    async def _persist_result(
        self,
        match: Match,
        innings: Innings,
        snapshot: ScoreSnapshot,
        state: MatchState,
        events: list[DomainEvent],
        *,
        user_id: UUID,
        client_event_id: UUID,
        base_revision: int,
        delivery: DeliveryCommand | None,
        legal_balls_before: int,
    ) -> None:
        persisted = await self._append_events(
            match,
            innings,
            events,
            user_id=user_id,
            client_event_id=client_event_id,
            base_revision=base_revision,
        )
        current = next(item for item in state.innings if item.innings_number == innings.innings_number)
        if delivery is not None:
            recorded = next(item for item in persisted if item.event_type is ScoringEventType.DELIVERY_RECORDED)
            self._add_delivery(innings, recorded, delivery, legal_balls_before, match.balls_per_over, state.rules)
        snapshot.revision = base_revision + 1
        self._fill_snapshot(snapshot, current)
        await self._replace_stats(innings.id, current)
        innings.status = current.status
        innings.target_runs = current.target_runs
        if current.status is InningsStatus.COMPLETED:
            innings.completed_at = utcnow()
            if innings.innings_number == 1:
                await self._ensure_second_innings(match, current)
        self._apply_match_result(match, state)
        await self._session.flush()

    async def _append_events(
        self,
        match: Match,
        innings: Innings,
        events: list[DomainEvent],
        *,
        user_id: UUID,
        client_event_id: UUID,
        base_revision: int,
    ) -> list[ScoringEvent]:
        sequence = await self._events.max_sequence(innings.id)
        stored: list[ScoringEvent] = []
        assigned_client_id = False
        for event in events:
            sequence += 1
            use_client_id = event.type in USER_EVENT_TYPES | {
                ScoringEventType.INNINGS_STARTED,
                ScoringEventType.DELIVERY_VOIDED,
            }
            row = ScoringEvent(
                match_id=match.id,
                innings_id=innings.id,
                sequence_number=sequence,
                client_event_id=client_event_id if use_client_id and not assigned_client_id else None,
                base_revision=base_revision,
                event_type=event.type,
                payload=event.payload,
                created_by_user_id=user_id,
            )
            if use_client_id and not assigned_client_id:
                assigned_client_id = True
            self._events.add(row)
            stored.append(row)
        try:
            async with self._session.begin_nested():
                await self._events.flush()
        except IntegrityError as exc:
            existing = await self._events.get_by_client_event_id(match.id, client_event_id)
            if existing is not None:
                raise AppError(
                    "DUPLICATE_EVENT",
                    "This scoring event was already recorded.",
                    status_code=409,
                ) from exc
            raise
        return stored

    def _add_delivery(
        self,
        innings: Innings,
        event: ScoringEvent,
        command: DeliveryCommand,
        legal_balls_before: int,
        balls_per_over: int,
        rules: MatchRules,
    ) -> None:
        over_number = legal_balls_before // balls_per_over + 1
        remainder = legal_balls_before % balls_per_over
        ball_in_over = remainder + 1 if command.is_legal else remainder
        payload = event.payload
        row = Delivery(
            innings_id=innings.id,
            scoring_event_id=event.id,
            sequence_number=event.sequence_number,
            over_number=over_number,
            ball_in_over=ball_in_over,
            striker_id=UUID(str(payload["striker_id"])),
            non_striker_id=UUID(str(payload["non_striker_id"])),
            bowler_id=UUID(str(payload["bowler_id"])),
            runs_off_bat=command.runs_off_bat,
            wides=command.wides,
            no_balls=command.no_balls,
            byes=command.byes,
            leg_byes=command.leg_byes,
            penalty_runs=command.penalty_runs,
            is_legal=command.is_legal,
        )
        self._deliveries.add(row)
        if command.dismissal is not None:
            self._dismissals.add(
                Dismissal(
                    delivery=row,
                    dismissed_player_id=command.dismissal.dismissed_player_id,
                    dismissal_type=command.dismissal.type,
                    fielder_id=command.dismissal.fielder_id,
                    credited_to_bowler=rules.bowler_credited(command.dismissal.type),
                )
            )

    async def _replace_stats(self, innings_id: UUID, innings: InningsState) -> None:
        await self._batting.replace_for_innings(
            innings_id,
            [
                InningsBattingStat(
                    innings_id=innings_id,
                    player_id=batter.player_id,
                    batting_position=batter.batting_position,
                    runs=batter.runs,
                    balls_faced=batter.balls_faced,
                    fours=batter.fours,
                    sixes=batter.sixes,
                    status=batter.status.value,
                    dismissal_type=batter.dismissal_type.value if batter.dismissal_type else None,
                )
                for batter in innings.batters.values()
            ],
        )
        await self._bowling.replace_for_innings(
            innings_id,
            [
                InningsBowlingStat(
                    innings_id=innings_id,
                    player_id=bowler.player_id,
                    legal_balls=bowler.legal_balls,
                    runs_conceded=bowler.runs_conceded,
                    wickets=bowler.wickets,
                    wides=bowler.wides,
                    no_balls=bowler.no_balls,
                    maidens=bowler.maidens,
                )
                for bowler in innings.bowlers.values()
            ],
        )

    def _fill_snapshot(self, snapshot: ScoreSnapshot, innings: InningsState) -> None:
        data = innings_to_dict(innings)
        snapshot.total_runs = innings.total_runs
        snapshot.wickets = innings.wickets
        snapshot.legal_balls = innings.legal_balls
        snapshot.striker_id = innings.striker_id
        snapshot.non_striker_id = innings.non_striker_id
        snapshot.current_bowler_id = innings.current_bowler_id
        snapshot.previous_bowler_id = innings.previous_bowler_id
        snapshot.needs_new_batter = innings.needs_new_batter
        snapshot.needs_new_bowler = innings.needs_new_bowler
        snapshot.target_runs = innings.target_runs
        snapshot.state_json = data

    async def _ensure_second_innings(self, match: Match, first: InningsState) -> None:
        existing = await self._innings.list_for_match(match.id)
        if any(item.innings_number == 2 for item in existing):
            return
        second = Innings(
            match_id=match.id,
            innings_number=2,
            batting_match_team_id=first.bowling_team_id,
            bowling_match_team_id=first.batting_team_id,
            status=InningsStatus.NOT_STARTED,
            target_runs=first.total_runs + 1,
        )
        self._innings.add(second)

    async def _drop_unstarted_later_innings(self, match: Match, current_number: int) -> None:
        for item in await self._innings.list_for_match(match.id):
            if item.innings_number > current_number and item.status is InningsStatus.NOT_STARTED:
                await self._innings.delete(item)

    def _apply_match_result(self, match: Match, state: MatchState) -> None:
        if state.status is MatchPlayStatus.COMPLETED:
            match.status = MatchStatus.COMPLETED
            if match.completed_at is None:
                match.completed_at = utcnow()
            match.result_type = state.result_type
            match.winner_match_team_id = state.winner_team_id
            match.margin_runs = state.margin_runs
            match.margin_wickets = state.margin_wickets

    async def _domain_state(self, match: Match) -> MatchState:
        batting_first, bowling_first = self._opening_sides(match)
        state = new_match_state(
            match_id=match.id,
            rules=self._rules(match),
            batting_first_team_id=batting_first.id,
            bowling_first_team_id=bowling_first.id,
        )
        if match.status is MatchStatus.COMPLETED:
            state.status = MatchPlayStatus.COMPLETED
            state.result_type = match.result_type
            state.winner_team_id = match.winner_match_team_id
            state.margin_runs = match.margin_runs
            state.margin_wickets = match.margin_wickets
        for innings in await self._innings.list_for_match(match.id):
            snapshot = await self._snapshots.get_for_innings(innings.id)
            if snapshot is None or not snapshot.state_json:
                continue
            state.innings.append(innings_from_dict(snapshot.state_json))
        return state

    async def _initial_state_for_innings(self, match: Match, innings: Innings) -> MatchState:
        batting_first, bowling_first = self._opening_sides(match)
        state = new_match_state(
            match_id=match.id,
            rules=self._rules(match),
            batting_first_team_id=batting_first.id,
            bowling_first_team_id=bowling_first.id,
        )
        if innings.innings_number == 1:
            return state
        first = next(item for item in await self._innings.list_for_match(match.id) if item.innings_number == 1)
        snapshot = await self._snapshots.get_for_innings(first.id)
        if snapshot is not None and snapshot.state_json:
            state.innings.append(innings_from_dict(snapshot.state_json))
        return state

    async def _live_state(self, match: Match, *, idempotent: bool = False) -> LiveMatchState:
        names = {item.id: item.display_name_snapshot for item in match.match_players}
        teams = {item.id: item for item in match.match_teams}
        innings_rows = await self._innings.list_for_match(match.id)
        pending = next((item for item in innings_rows if item.status is InningsStatus.NOT_STARTED), None)
        current_row = next((item for item in reversed(innings_rows) if item.status is InningsStatus.LIVE), None)
        if current_row is None:
            current_row = next(
                (item for item in reversed(innings_rows) if item.status is InningsStatus.COMPLETED),
                None,
            )
        snapshot = await self._snapshots.get_for_innings(current_row.id) if current_row else None
        innings_state = innings_from_dict(snapshot.state_json) if snapshot and snapshot.state_json else None
        rules = self._rules(match)
        live_innings = None
        striker = non_striker = bowler = None
        current_over: list[CurrentOverBall] = []
        if current_row is not None and innings_state is not None and snapshot is not None:
            batting = teams[current_row.batting_match_team_id]
            bowling = teams[current_row.bowling_match_team_id]
            live_innings = LiveInnings(
                id=current_row.id,
                number=current_row.innings_number,
                status=current_row.status,
                batting_team=LiveTeam(match_team_id=batting.id, name=batting.team_name_snapshot),
                bowling_team=LiveTeam(match_team_id=bowling.id, name=bowling.team_name_snapshot),
                runs=innings_state.total_runs,
                wickets=innings_state.wickets,
                legal_balls=innings_state.legal_balls,
                overs=format_overs(innings_state.legal_balls, rules.balls_per_over),
                balls_remaining=balls_remaining(rules.maximum_legal_balls, innings_state.legal_balls),
                current_run_rate=run_rate(innings_state.total_runs, innings_state.legal_balls, rules.balls_per_over),
                target=innings_state.target_runs,
                required_runs=required_runs(innings_state.target_runs, innings_state.total_runs),
                required_run_rate=required_run_rate(
                    target_runs=innings_state.target_runs,
                    current_runs=innings_state.total_runs,
                    maximum_legal_balls=rules.maximum_legal_balls,
                    legal_balls=innings_state.legal_balls,
                    balls_per_over=rules.balls_per_over,
                ),
            )
            if innings_state.striker_id:
                batter = innings_state.batters[innings_state.striker_id]
                striker = self._batter_card(batter, names, is_striker=True)
            if innings_state.non_striker_id:
                batter = innings_state.batters[innings_state.non_striker_id]
                non_striker = self._batter_card(batter, names, is_striker=False)
            if innings_state.current_bowler_id:
                bowl = innings_state.bowlers[innings_state.current_bowler_id]
                bowler = LiveBowlerCard(
                    match_player_id=bowl.player_id,
                    name=names.get(bowl.player_id, ""),
                    overs=format_overs(bowl.legal_balls, rules.balls_per_over),
                    legal_balls=bowl.legal_balls,
                    runs=bowl.runs_conceded,
                    wickets=bowl.wickets,
                    economy=economy(bowl.runs_conceded, bowl.legal_balls, rules.balls_per_over),
                    wides=bowl.wides,
                    no_balls=bowl.no_balls,
                )
            current_over = [
                CurrentOverBall(label=item.label, runs=item.runs, wicket=item.wicket, legal=item.legal)
                for item in innings_state.current_over
            ]
        return LiveMatchState(
            match_id=match.id,
            status=match.status,
            revision=snapshot.revision if snapshot else 0,
            innings=live_innings,
            striker=striker,
            non_striker=non_striker,
            bowler=bowler,
            current_over=current_over,
            needs_new_batter=bool(innings_state.needs_new_batter) if innings_state else False,
            needs_new_bowler=bool(innings_state.needs_new_bowler) if innings_state else False,
            needs_openers=pending is not None and match.status is MatchStatus.LIVE,
            pending_innings_id=pending.id if pending is not None else None,
            chase_target=pending.target_runs if pending is not None else None,
            available_batters=self._available_batters(innings_state, names) if innings_state else [],
            available_bowlers=self._available_bowlers(innings_state, names, rules) if innings_state else [],
            result_type=match.result_type,
            winner_match_team_id=match.winner_match_team_id,
            margin_runs=match.margin_runs,
            margin_wickets=match.margin_wickets,
            idempotent=idempotent,
        )

    def _batter_card(self, batter, names: dict[UUID, str], *, is_striker: bool) -> LiveBatterCard:
        return LiveBatterCard(
            match_player_id=batter.player_id,
            name=names.get(batter.player_id, ""),
            runs=batter.runs,
            balls=batter.balls_faced,
            fours=batter.fours,
            sixes=batter.sixes,
            strike_rate=strike_rate(batter.runs, batter.balls_faced),
            is_striker=is_striker,
        )

    def _available_batters(self, innings: InningsState, names: dict[UUID, str]) -> list[LiveBatterOption]:
        crease = {innings.striker_id, innings.non_striker_id} - {None}
        options: list[LiveBatterOption] = []
        for player_id in innings.batting_player_ids:
            batter = innings.batters.get(player_id)
            status = "AVAILABLE"
            selectable = True
            runs = 0
            balls = 0
            if batter is not None:
                runs = batter.runs
                balls = batter.balls_faced
                if batter.status is BatterStatus.OUT:
                    status = "OUT"
                    selectable = False
                elif batter.status is BatterStatus.RETIRED_OUT:
                    status = "RETIRED_OUT"
                    selectable = False
                elif batter.status is BatterStatus.RETIRED_HURT:
                    status = "RETIRED_HURT"
                    selectable = player_id not in crease
                elif player_id in crease:
                    status = "BATTING"
                    selectable = False
            elif player_id in crease:
                status = "BATTING"
                selectable = False
            if player_id in crease and status == "AVAILABLE":
                status = "BATTING"
                selectable = False
            options.append(
                LiveBatterOption(
                    match_player_id=player_id,
                    name=names.get(player_id, ""),
                    selectable=selectable,
                    status=status,
                    runs=runs,
                    balls=balls,
                )
            )
        return options

    def _available_bowlers(
        self,
        innings: InningsState,
        names: dict[UUID, str],
        rules: MatchRules,
    ) -> list[LiveBowlerOption]:
        options: list[LiveBowlerOption] = []
        for player_id in innings.bowling_player_ids:
            bowler = innings.bowlers.get(player_id, BowlerState(player_id=player_id))
            reason: str | None = None
            selectable = True
            if rules.enforce_consecutive_overs and player_id == innings.previous_bowler_id:
                selectable = False
                reason = "CONSECUTIVE_OVER"
            elif bowler.legal_balls >= rules.bowler_max_legal_balls:
                selectable = False
                reason = "OVER_LIMIT"
            options.append(
                LiveBowlerOption(
                    match_player_id=player_id,
                    name=names.get(player_id, ""),
                    selectable=selectable,
                    unavailable_reason=reason,
                    overs=format_overs(bowler.legal_balls, rules.balls_per_over),
                    legal_balls=bowler.legal_balls,
                    runs=bowler.runs_conceded,
                    wickets=bowler.wickets,
                    economy=economy(bowler.runs_conceded, bowler.legal_balls, rules.balls_per_over),
                )
            )
        return options

    async def _lock_owned(self, match_id: UUID, user_id: UUID) -> Match:
        locked = await self._matches.get_owned_for_update(match_id, user_id)
        if locked is None:
            raise MatchNotFoundError()
        return await self._owned_detail(match_id, user_id)

    async def _lock_live(self, match_id: UUID, user_id: UUID) -> tuple[Match, Innings, ScoreSnapshot]:
        match = await self._lock_owned(match_id, user_id)
        if match.status is MatchStatus.COMPLETED:
            raise AppError("MATCH_COMPLETE", "This match is complete.", status_code=409)
        if match.status is not MatchStatus.LIVE:
            raise MatchNotLiveError()
        innings_rows = await self._innings.list_for_match(match.id)
        live = next((item for item in innings_rows if item.status is InningsStatus.LIVE), None)
        if live is None:
            raise AppError("INNINGS_NOT_LIVE", "No live innings is available to score.", status_code=409)
        locked_innings = await self._innings.get_for_update(live.id)
        snapshot = await self._snapshots.get_for_update(live.id)
        if locked_innings is None or snapshot is None:
            raise AppError("INNINGS_NOT_LIVE", "No live innings is available to score.", status_code=409)
        return match, locked_innings, snapshot

    async def _undo_innings(self, match: Match) -> Innings:
        rows = await self._innings.list_for_match(match.id)
        live = next((item for item in rows if item.status is InningsStatus.LIVE), None)
        if live is not None:
            locked = await self._innings.get_for_update(live.id)
            if locked is None:
                raise NothingToUndoError()
            return locked
        pending = next((item for item in rows if item.status is InningsStatus.NOT_STARTED), None)
        completed = next((item for item in reversed(rows) if item.status is InningsStatus.COMPLETED), None)
        if pending is not None and completed is not None:
            locked = await self._innings.get_for_update(completed.id)
            if locked is None:
                raise NothingToUndoError()
            return locked
        raise NothingToUndoError()

    async def _duplicate_or_conflict(
        self,
        match: Match,
        snapshot: ScoreSnapshot,
        client_event_id: UUID,
        base_revision: int,
    ) -> LiveMatchState | None:
        existing = await self._events.get_by_client_event_id(match.id, client_event_id)
        if existing is not None:
            return await self._live_state(match, idempotent=True)
        if base_revision != snapshot.revision:
            raise ScoreConflictError(snapshot.revision)
        return None

    async def _owned_detail(self, match_id: UUID, user_id: UUID) -> Match:
        match = await self._matches.get_owned_with_participants(match_id, user_id)
        if match is None:
            raise MatchNotFoundError()
        return match

    def _rules(self, match: Match) -> MatchRules:
        return MatchRules.from_match(
            overs_per_innings=match.overs_per_innings,
            balls_per_over=match.balls_per_over,
            players_per_team=match.players_per_team,
            format=match.format.value,
        )

    def _opening_sides(self, match: Match) -> tuple[MatchTeam, MatchTeam]:
        teams = {item.id: item for item in match.match_teams}
        if match.toss_winner_match_team_id is None or match.toss_decision is None:
            raise MatchNotReadyToStartError()
        winner = teams[match.toss_winner_match_team_id]
        other = next(item for item in match.match_teams if item.id != winner.id)
        if match.toss_decision is TossDecision.BAT:
            return winner, other
        return other, winner

    def _team(self, match: Match, match_team_id: UUID) -> MatchTeam:
        return next(item for item in match.match_teams if item.id == match_team_id)

    def _xi_ids(self, match: Match, match_team_id: UUID) -> tuple[UUID, ...]:
        return tuple(item.id for item in match.match_players if item.match_team_id == match_team_id and item.is_playing)

    def _validate_openers(
        self,
        match: Match,
        batting: MatchTeam,
        bowling: MatchTeam,
        payload: StartMatchRequest,
    ) -> None:
        batting_ids = set(self._xi_ids(match, batting.id))
        bowling_ids = set(self._xi_ids(match, bowling.id))
        if payload.striker_id not in batting_ids or payload.non_striker_id not in batting_ids:
            raise AppError("INVALID_NEXT_BATTER", "Opening batters must be in the batting Playing XI.", status_code=400)
        if payload.striker_id == payload.non_striker_id:
            raise AppError("INVALID_NEXT_BATTER", "Striker and non-striker must be different.", status_code=400)
        if payload.bowler_id not in bowling_ids:
            raise AppError("INVALID_BOWLER", "Bowler must be in the bowling Playing XI.", status_code=400)

    def _delivery_command(self, payload: DeliveryPayload, snapshot: ScoreSnapshot) -> DeliveryCommand:
        dismissal = None
        if payload.dismissal is not None:
            dismissed = payload.dismissal.dismissed_player_id or snapshot.striker_id
            if dismissed is None:
                raise AppError("INVALID_DISMISSAL", "A dismissed batter is required.", status_code=400)
            dismissal = DismissalCommand(
                type=payload.dismissal.type,
                dismissed_player_id=dismissed,
                fielder_id=payload.dismissal.fielder_id,
                crossed=payload.dismissal.crossed,
            )
        return DeliveryCommand(
            runs_off_bat=payload.runs_off_bat,
            wides=payload.wides,
            no_balls=payload.no_balls,
            byes=payload.byes,
            leg_byes=payload.leg_byes,
            penalty_runs=payload.penalty_runs,
            dismissal=dismissal,
        )

    def _to_domain_event(self, row: ScoringEvent) -> DomainEvent:
        return DomainEvent(row.event_type, dict(row.payload), sequence_number=row.sequence_number)

    def _raise_engine(self, exc: CricketEngineError) -> NoReturn:
        status = 409 if exc.code in CONFLICT_CODES else 400
        raise AppError(exc.code, exc.message, status_code=status) from exc

    def _log(self, event: str, **fields: object) -> None:
        logger.info(event, **fields)

    def _ms(self, start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)
