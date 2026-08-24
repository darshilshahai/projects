from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.dismissals import format_dismissal
from app.analytics.extras import calculate_extras
from app.analytics.overs import build_over_summaries
from app.analytics.partnerships import build_partnerships
from app.analytics.summary import BatterSummaryInput, BowlerSummaryInput, build_match_summary
from app.analytics.types import DeliveryFact
from app.core.exceptions import MatchNotFoundError
from app.cricket.formatters import (
    economy,
    format_overs,
    required_run_rate,
    run_rate,
    scorecard_rate,
    strike_rate,
)
from app.cricket.serialization import innings_from_dict
from app.cricket.state import InningsState
from app.cricket.types import InningsStatus
from app.models.delivery import Delivery
from app.models.innings import Innings
from app.models.innings_stats import InningsBattingStat, InningsBowlingStat
from app.models.match import Match
from app.models.match_team import MatchTeam
from app.repositories.match import MatchRepository
from app.repositories.scoring import (
    BattingStatsRepository,
    BowlingStatsRepository,
    DeliveryRepository,
    InningsRepository,
    ScoreSnapshotRepository,
)
from app.schemas.scorecard import (
    BattingScorecardRow,
    BowlingScorecardRow,
    ExtrasScorecard,
    FallOfWicketRow,
    InningsScorecard,
    MatchScorecardResponse,
    MatchScorecardSummary,
    NamedScorecardStat,
    OverDeliveryRow,
    OverSummaryRow,
    PartnershipRow,
    ScorecardMatchHeader,
    ScorecardTeam,
    YetToBatRow,
)


class ScorecardService:
    def __init__(self, session: AsyncSession) -> None:
        self._matches = MatchRepository(session)
        self._innings = InningsRepository(session)
        self._deliveries = DeliveryRepository(session)
        self._snapshots = ScoreSnapshotRepository(session)
        self._batting = BattingStatsRepository(session)
        self._bowling = BowlingStatsRepository(session)

    async def get_match_scorecard(self, match_id: UUID, user_id: UUID) -> MatchScorecardResponse:
        match = await self._matches.get_owned_with_participants(match_id, user_id)
        if match is None:
            raise MatchNotFoundError()
        names = {item.id: item.display_name_snapshot for item in match.match_players}
        teams = {item.id: item for item in match.match_teams}
        innings_rows = [
            item
            for item in await self._innings.list_for_match(match.id)
            if item.status is not InningsStatus.NOT_STARTED
        ]
        innings_ids = [item.id for item in innings_rows]
        snapshots = {item.innings_id: item for item in await self._snapshots.list_for_innings_ids(innings_ids)}
        batting_rows = await self._batting.list_for_innings_ids(innings_ids)
        bowling_rows = await self._bowling.list_for_innings_ids(innings_ids)
        deliveries = await self._deliveries.list_active_for_innings_ids(innings_ids)
        batting_by_innings: dict[UUID, list[InningsBattingStat]] = defaultdict(list)
        bowling_by_innings: dict[UUID, list[InningsBowlingStat]] = defaultdict(list)
        deliveries_by_innings: dict[UUID, list[Delivery]] = defaultdict(list)
        for batting_row in batting_rows:
            batting_by_innings[batting_row.innings_id].append(batting_row)
        for bowling_row in bowling_rows:
            bowling_by_innings[bowling_row.innings_id].append(bowling_row)
        for delivery in deliveries:
            deliveries_by_innings[delivery.innings_id].append(delivery)

        cards: list[InningsScorecard] = []
        for innings in innings_rows:
            snapshot = snapshots.get(innings.id)
            state = innings_from_dict(snapshot.state_json) if snapshot and snapshot.state_json else None
            cards.append(
                self._innings_card(
                    match=match,
                    innings=innings,
                    state=state,
                    teams=teams,
                    names=names,
                    batting=batting_by_innings[innings.id],
                    bowling=bowling_by_innings[innings.id],
                    deliveries=deliveries_by_innings[innings.id],
                )
            )

        live = next((item for item in cards if item.status is InningsStatus.LIVE), None)
        current_number = live.number if live is not None else (cards[-1].number if cards else None)
        return MatchScorecardResponse(
            match=self._header(match, teams),
            status=match.status,
            current_innings_number=current_number,
            innings=cards,
            summary=self._summary(cards),
        )

    def _header(self, match: Match, teams: dict[UUID, MatchTeam]) -> ScorecardMatchHeader:
        ordered = sorted(teams.values(), key=lambda item: item.side.value)
        team_a = self._team(ordered[0]) if ordered else None
        team_b = self._team(ordered[1]) if len(ordered) > 1 else None
        winner = teams.get(match.winner_match_team_id) if match.winner_match_team_id else None
        return ScorecardMatchHeader(
            id=match.id,
            name=match.name,
            format=match.format,
            status=match.status,
            venue_name=match.venue_name,
            overs_per_innings=match.overs_per_innings,
            balls_per_over=match.balls_per_over,
            players_per_team=match.players_per_team,
            team_a=team_a,
            team_b=team_b,
            result_type=match.result_type,
            winner_match_team_id=match.winner_match_team_id,
            winner_name=winner.team_name_snapshot if winner is not None else None,
            margin_runs=match.margin_runs,
            margin_wickets=match.margin_wickets,
        )

    def _innings_card(
        self,
        *,
        match: Match,
        innings: Innings,
        state: InningsState | None,
        teams: dict[UUID, MatchTeam],
        names: dict[UUID, str],
        batting: list[InningsBattingStat],
        bowling: list[InningsBowlingStat],
        deliveries: list[Delivery],
    ) -> InningsScorecard:
        batting_team = teams[innings.batting_match_team_id]
        bowling_team = teams[innings.bowling_match_team_id]
        facts = [_delivery_fact(item) for item in deliveries]
        extras = calculate_extras(facts)
        balls_per_over = match.balls_per_over
        runs = state.total_runs if state is not None else innings_total_from_facts(facts)
        wickets = state.wickets if state is not None else sum(1 for item in facts if item.is_team_wicket)
        legal_balls = state.legal_balls if state is not None else sum(1 for item in facts if item.is_legal)
        target = state.target_runs if state is not None else innings.target_runs
        striker_id = state.striker_id if state is not None else None
        non_striker_id = state.non_striker_id if state is not None else None
        dismissal_by_player = {
            item.dismissed_player_id: item
            for item in facts
            if item.dismissed_player_id is not None and item.dismissal_type is not None
        }
        batting_sorted = sorted(batting, key=lambda item: item.batting_position)
        batting_ids = {item.player_id for item in batting_sorted}
        xi = [player for player in match.match_players if player.match_team_id == batting_team.id and player.is_playing]
        yet_to_bat = [
            YetToBatRow(match_player_id=player.id, name=player.display_name_snapshot)
            for player in xi
            if player.id not in batting_ids
        ]
        first_bowl: dict[UUID, int] = {}
        for index, item in enumerate(facts):
            first_bowl.setdefault(item.bowler_id, index)
        bowling_sorted = sorted(
            bowling,
            key=lambda item: (first_bowl.get(item.player_id, 10_000), names.get(item.player_id, "")),
        )
        opening = None
        if state is not None and state.striker_id and state.non_striker_id and not facts:
            opening = (state.striker_id, state.non_striker_id)
        elif facts:
            opening = (facts[0].striker_id, facts[0].non_striker_id)
        partnerships = build_partnerships(
            facts,
            innings_complete=innings.status is InningsStatus.COMPLETED,
            opening=opening,
        )
        fall = []
        if state is not None:
            fall = [
                FallOfWicketRow(
                    wicket_number=item.wicket_number,
                    score=item.team_score,
                    player_id=item.player_id,
                    player_name=names.get(item.player_id, ""),
                    legal_balls=item.legal_balls,
                    overs=format_overs(item.legal_balls, balls_per_over),
                )
                for item in sorted(state.fall_of_wickets, key=lambda item: item.wicket_number)
            ]
        return InningsScorecard(
            id=innings.id,
            number=innings.innings_number,
            status=innings.status,
            batting_team=self._team(batting_team),
            bowling_team=self._team(bowling_team),
            runs=runs,
            wickets=wickets,
            legal_balls=legal_balls,
            overs=format_overs(legal_balls, balls_per_over),
            run_rate=scorecard_rate(run_rate(runs, legal_balls, balls_per_over)),
            required_run_rate=_required_rate(
                target=target,
                runs=runs,
                legal_balls=legal_balls,
                overs_per_innings=match.overs_per_innings,
                balls_per_over=balls_per_over,
            ),
            target=target,
            all_out=wickets >= max(match.players_per_team - 1, 0),
            extras=ExtrasScorecard(
                total=extras.total,
                wides=extras.wides,
                no_balls=extras.no_balls,
                byes=extras.byes,
                leg_byes=extras.leg_byes,
                penalty_runs=extras.penalty_runs,
            ),
            batting=[
                self._batting_row(
                    row,
                    names=names,
                    facts=dismissal_by_player,
                    striker_id=striker_id,
                    non_striker_id=non_striker_id,
                )
                for row in batting_sorted
            ],
            yet_to_bat=yet_to_bat,
            bowling=[self._bowling_row(row, names=names, balls_per_over=balls_per_over) for row in bowling_sorted],
            fall_of_wickets=fall,
            partnerships=[
                PartnershipRow(
                    batter_1_id=item.batter_1_id,
                    batter_1_name=names.get(item.batter_1_id, ""),
                    batter_2_id=item.batter_2_id,
                    batter_2_name=names.get(item.batter_2_id, ""),
                    runs=item.runs,
                    legal_balls=item.legal_balls,
                    start_score=item.start_score,
                    end_score=item.end_score,
                    is_current=item.is_current,
                    batter_1_runs=item.batter_1_runs,
                    batter_2_runs=item.batter_2_runs,
                )
                for item in partnerships
            ],
            overs_summary=[
                OverSummaryRow(
                    over_number=item.over_number,
                    runs=item.runs,
                    wickets=item.wickets,
                    legal_balls=item.legal_balls,
                    is_complete=item.is_complete,
                    deliveries=[
                        OverDeliveryRow(
                            label=ball.label,
                            runs=ball.runs,
                            wicket=ball.wicket,
                            legal=ball.legal,
                        )
                        for ball in item.deliveries
                    ],
                )
                for item in build_over_summaries(facts, balls_per_over=balls_per_over)
            ],
        )

    def _batting_row(
        self,
        row: InningsBattingStat,
        *,
        names: dict[UUID, str],
        facts: dict[UUID, DeliveryFact],
        striker_id: UUID | None,
        non_striker_id: UUID | None,
    ) -> BattingScorecardRow:
        dismissal = facts.get(row.player_id)
        bowler_name = names.get(dismissal.bowler_id) if dismissal is not None else None
        fielder_name = names.get(dismissal.fielder_id) if dismissal is not None and dismissal.fielder_id else None
        return BattingScorecardRow(
            match_player_id=row.player_id,
            name=names.get(row.player_id, ""),
            batting_position=row.batting_position,
            runs=row.runs,
            balls=row.balls_faced,
            fours=row.fours,
            sixes=row.sixes,
            strike_rate=scorecard_rate(strike_rate(row.runs, row.balls_faced)),
            status=row.status,
            dismissal_text=format_dismissal(
                status=row.status,
                dismissal_type=row.dismissal_type,
                bowler_name=bowler_name,
                fielder_name=fielder_name,
            ),
            is_striker=row.player_id == striker_id,
            is_non_striker=row.player_id == non_striker_id,
        )

    def _bowling_row(
        self,
        row: InningsBowlingStat,
        *,
        names: dict[UUID, str],
        balls_per_over: int,
    ) -> BowlingScorecardRow:
        return BowlingScorecardRow(
            match_player_id=row.player_id,
            name=names.get(row.player_id, ""),
            legal_balls=row.legal_balls,
            overs=format_overs(row.legal_balls, balls_per_over),
            maidens=row.maidens,
            runs_conceded=row.runs_conceded,
            wickets=row.wickets,
            economy=scorecard_rate(economy(row.runs_conceded, row.legal_balls, balls_per_over)),
            wides=row.wides,
            no_balls=row.no_balls,
        )

    def _summary(self, innings: list[InningsScorecard]) -> MatchScorecardSummary:
        facts = build_match_summary(
            batting=[
                BatterSummaryInput(
                    match_player_id=row.match_player_id,
                    name=row.name,
                    runs=row.runs,
                    fours=row.fours,
                    sixes=row.sixes,
                )
                for card in innings
                for row in card.batting
            ],
            bowling=[
                BowlerSummaryInput(
                    match_player_id=row.match_player_id,
                    name=row.name,
                    wickets=row.wickets,
                    runs_conceded=row.runs_conceded,
                )
                for card in innings
                for row in card.bowling
            ],
            partnerships=[
                (
                    _partnership_fact(row),
                    f"{row.batter_1_name} & {row.batter_2_name}",
                )
                for card in innings
                for row in card.partnerships
            ],
            extras_total=sum(card.extras.total for card in innings),
        )
        return MatchScorecardSummary(
            highest_scorers=[_named(item) for item in facts.highest_scorers],
            most_wickets=[_named(item) for item in facts.most_wickets],
            total_boundaries=facts.total_boundaries,
            total_sixes=facts.total_sixes,
            total_extras=facts.total_extras,
            largest_partnerships=[_named(item) for item in facts.largest_partnerships],
        )

    def _team(self, team: MatchTeam) -> ScorecardTeam:
        return ScorecardTeam(
            match_team_id=team.id,
            name=team.team_name_snapshot,
            short_name=team.team_short_name_snapshot,
        )


def _delivery_fact(row: Delivery) -> DeliveryFact:
    dismissal = row.dismissal
    return DeliveryFact(
        sequence_number=row.sequence_number,
        over_number=row.over_number,
        striker_id=row.striker_id,
        non_striker_id=row.non_striker_id,
        bowler_id=row.bowler_id,
        runs_off_bat=row.runs_off_bat,
        wides=row.wides,
        no_balls=row.no_balls,
        byes=row.byes,
        leg_byes=row.leg_byes,
        penalty_runs=row.penalty_runs,
        is_legal=row.is_legal,
        dismissal_type=dismissal.dismissal_type if dismissal is not None else None,
        dismissed_player_id=dismissal.dismissed_player_id if dismissal is not None else None,
        fielder_id=dismissal.fielder_id if dismissal is not None else None,
        credited_to_bowler=dismissal.credited_to_bowler if dismissal is not None else False,
    )


def _required_rate(
    *,
    target: int | None,
    runs: int,
    legal_balls: int,
    overs_per_innings: int,
    balls_per_over: int,
) -> float | None:
    if target is None:
        return None
    value = required_run_rate(
        target_runs=target,
        current_runs=runs,
        maximum_legal_balls=overs_per_innings * balls_per_over,
        legal_balls=legal_balls,
        balls_per_over=balls_per_over,
    )
    if value is None:
        return None
    return scorecard_rate(value)


def innings_total_from_facts(facts: list[DeliveryFact]) -> int:
    return sum(item.team_runs for item in facts)


def _partnership_fact(row: PartnershipRow):
    from app.analytics.types import PartnershipFact

    return PartnershipFact(
        batter_1_id=row.batter_1_id,
        batter_2_id=row.batter_2_id,
        runs=row.runs,
        legal_balls=row.legal_balls,
        start_score=row.start_score,
        end_score=row.end_score,
        is_current=row.is_current,
        batter_1_runs=row.batter_1_runs,
        batter_2_runs=row.batter_2_runs,
    )


def _named(item) -> NamedScorecardStat:
    return NamedScorecardStat(
        match_player_id=item.match_player_id,
        name=item.name,
        value=item.value,
    )
