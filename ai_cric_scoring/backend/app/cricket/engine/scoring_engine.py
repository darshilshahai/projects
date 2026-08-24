from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from app.cricket.commands import DeliveryCommand, RetireCommand, SelectBatterCommand, SelectBowlerCommand
from app.cricket.events import DomainEvent
from app.cricket.exceptions import (
    BatterSelectionRequiredError,
    BowlerSelectionRequiredError,
    InningsCompleteError,
    InningsStateError,
    InvalidBowlerError,
    InvalidDismissalError,
    InvalidNextBatterError,
    MatchCompleteError,
)
from app.cricket.formatters import over_label
from app.cricket.rules import MatchRules
from app.cricket.state import (
    BatterState,
    BowlerState,
    FallOfWicket,
    InningsState,
    MatchState,
    OverBall,
    PartnershipState,
)
from app.cricket.types import (
    STRIKER_ONLY_DISMISSALS,
    DismissalType,
    InningsStatus,
    MatchPlayStatus,
    ResultType,
    ScoringEventType,
)
from app.cricket.validator import validate_delivery


class EngineResult:
    def __init__(self, state: MatchState, events: list[DomainEvent]) -> None:
        self.state = state
        self.events = events


class ScoringEngine:
    def start_innings(
        self,
        state: MatchState,
        *,
        innings_number: int,
        batting_team_id: UUID,
        bowling_team_id: UUID,
        batting_player_ids: tuple[UUID, ...],
        bowling_player_ids: tuple[UUID, ...],
        striker_id: UUID,
        non_striker_id: UUID,
        bowler_id: UUID,
        target_runs: int | None = None,
    ) -> EngineResult:
        next_state = deepcopy(state)
        if next_state.status == MatchPlayStatus.COMPLETED:
            raise MatchCompleteError()
        self._validate_openers(
            batting_player_ids,
            bowling_player_ids,
            striker_id,
            non_striker_id,
            bowler_id,
        )
        innings = InningsState(
            innings_number=innings_number,
            batting_team_id=batting_team_id,
            bowling_team_id=bowling_team_id,
            batting_player_ids=batting_player_ids,
            bowling_player_ids=bowling_player_ids,
            target_runs=target_runs,
            striker_id=striker_id,
            non_striker_id=non_striker_id,
            current_bowler_id=bowler_id,
            batters={
                striker_id: BatterState(player_id=striker_id, batting_position=1),
                non_striker_id: BatterState(player_id=non_striker_id, batting_position=2),
            },
            bowlers={bowler_id: BowlerState(player_id=bowler_id)},
            current_partnership=PartnershipState(
                batter_1_id=striker_id,
                batter_2_id=non_striker_id,
                start_score=0,
            ),
        )
        next_state.innings.append(innings)
        return EngineResult(
            next_state,
            [
                DomainEvent(
                    ScoringEventType.INNINGS_STARTED,
                    {
                        "innings_number": innings_number,
                        "batting_team_id": str(batting_team_id),
                        "bowling_team_id": str(bowling_team_id),
                        "batting_player_ids": [str(item) for item in batting_player_ids],
                        "bowling_player_ids": [str(item) for item in bowling_player_ids],
                        "striker_id": str(striker_id),
                        "non_striker_id": str(non_striker_id),
                        "bowler_id": str(bowler_id),
                        "target_runs": target_runs,
                    },
                )
            ],
        )

    def apply_delivery(self, state: MatchState, command: DeliveryCommand) -> EngineResult:
        next_state = deepcopy(state)
        innings = self._require_live_innings(next_state)
        if innings.needs_new_batter:
            raise BatterSelectionRequiredError()
        if innings.needs_new_bowler or innings.current_bowler_id is None:
            raise BowlerSelectionRequiredError()
        validate_delivery(command)
        original_striker = innings.striker_id
        original_non_striker = innings.non_striker_id
        bowler_id = innings.current_bowler_id
        if original_striker is None or original_non_striker is None or bowler_id is None:
            raise InningsStateError("Opening batters and bowler must be set.")
        self._validate_dismissal_players(command, original_striker, original_non_striker, innings)

        striker = innings.batters[original_striker]
        bowler = innings.bowlers.setdefault(bowler_id, BowlerState(player_id=bowler_id))
        team_runs = command.team_runs
        legal = command.is_legal
        bowler_runs = command.bowler_conceded(penalty_charged_to_bowler=next_state.rules.penalty_runs_charged_to_bowler)

        innings.total_runs += team_runs
        if legal:
            innings.legal_balls += 1
            bowler.legal_balls += 1
        bowler.runs_conceded += bowler_runs
        bowler.wides += command.wides
        bowler.no_balls += command.no_balls
        bowler.current_over_conceded += bowler_runs
        if command.wides == 0:
            striker.balls_faced += 1
        striker.runs += command.runs_off_bat
        if command.runs_off_bat == 4:
            striker.fours += 1
        elif command.runs_off_bat == 6:
            striker.sixes += 1
        if innings.current_partnership is not None:
            innings.current_partnership.runs += team_runs
            if legal:
                innings.current_partnership.legal_balls += 1

        innings.current_over.append(
            OverBall(
                label=over_label(
                    runs_off_bat=command.runs_off_bat,
                    wides=command.wides,
                    no_balls=command.no_balls,
                    byes=command.byes,
                    leg_byes=command.leg_byes,
                    penalty_runs=command.penalty_runs,
                    wicket=command.dismissal is not None,
                    team_runs=team_runs,
                ),
                runs=team_runs,
                wicket=command.dismissal is not None,
                legal=legal,
            )
        )

        if command.running_runs() % 2 == 1:
            self._swap_ends(innings)

        if command.dismissal is not None:
            if command.dismissal.type == DismissalType.RUN_OUT and command.dismissal.crossed:
                self._swap_ends(innings)
            self._apply_wicket(next_state, innings, command.dismissal.type, command.dismissal.dismissed_player_id)

        over_complete = legal and innings.legal_balls > 0 and innings.legal_balls % next_state.rules.balls_per_over == 0
        innings_done = self._innings_should_complete(next_state, innings)
        if over_complete and not innings_done:
            if bowler.current_over_conceded == 0:
                bowler.maidens += 1
            bowler.current_over_conceded = 0
            self._swap_ends(innings)
            innings.previous_bowler_id = bowler_id
            innings.current_bowler_id = None
            innings.needs_new_bowler = True
        elif over_complete:
            if bowler.current_over_conceded == 0:
                bowler.maidens += 1
            bowler.current_over_conceded = 0

        events = [
            DomainEvent(
                ScoringEventType.DELIVERY_RECORDED,
                {
                    "runs_off_bat": command.runs_off_bat,
                    "wides": command.wides,
                    "no_balls": command.no_balls,
                    "byes": command.byes,
                    "leg_byes": command.leg_byes,
                    "penalty_runs": command.penalty_runs,
                    "is_legal": legal,
                    "team_runs": team_runs,
                    "striker_id": str(original_striker),
                    "non_striker_id": str(original_non_striker),
                    "bowler_id": str(bowler_id),
                    "dismissal": None
                    if command.dismissal is None
                    else {
                        "type": command.dismissal.type.value,
                        "dismissed_player_id": str(command.dismissal.dismissed_player_id),
                        "fielder_id": str(command.dismissal.fielder_id) if command.dismissal.fielder_id else None,
                        "crossed": command.dismissal.crossed,
                    },
                },
            )
        ]
        events.extend(self._complete_if_needed(next_state, innings))
        return EngineResult(next_state, events)

    def select_batter(self, state: MatchState, command: SelectBatterCommand) -> EngineResult:
        next_state = deepcopy(state)
        innings = self._require_live_innings(next_state)
        if not innings.needs_new_batter:
            raise InvalidNextBatterError("A new batter is not required.")
        player_id = command.player_id
        if player_id not in innings.batting_player_ids:
            raise InvalidNextBatterError("Batter must belong to the batting Playing XI.")
        if player_id in {innings.striker_id, innings.non_striker_id}:
            raise InvalidNextBatterError("That batter is already at the crease.")
        existing = innings.batters.get(player_id)
        if existing is not None and existing.is_out:
            raise InvalidNextBatterError("That batter is already dismissed.")
        if existing is not None and existing.is_retired_out:
            raise InvalidNextBatterError("A retired-out batter cannot return.")
        if existing is not None and existing.is_retired_hurt:
            existing.is_retired_hurt = False
            batter = existing
        else:
            batter = BatterState(player_id=player_id, batting_position=innings.next_batting_position)
            innings.next_batting_position += 1
            innings.batters[player_id] = batter
        if innings.vacant_end == "non_striker" or innings.striker_id is not None:
            innings.non_striker_id = player_id
        else:
            innings.striker_id = player_id
        if innings.striker_id is None or innings.non_striker_id is None:
            raise InvalidNextBatterError("Both crease ends could not be filled.")
        innings.current_partnership = PartnershipState(
            batter_1_id=innings.striker_id,
            batter_2_id=innings.non_striker_id,
            start_score=innings.total_runs,
        )
        innings.needs_new_batter = False
        innings.vacant_end = None
        return EngineResult(
            next_state,
            [DomainEvent(ScoringEventType.BATTER_SELECTED, {"player_id": str(player_id)})],
        )

    def select_bowler(self, state: MatchState, command: SelectBowlerCommand) -> EngineResult:
        next_state = deepcopy(state)
        innings = self._require_live_innings(next_state)
        if not innings.needs_new_bowler:
            raise InvalidBowlerError("A new bowler is not required.")
        player_id = command.player_id
        if player_id not in innings.bowling_player_ids:
            raise InvalidBowlerError("Bowler must belong to the bowling Playing XI.")
        if next_state.rules.enforce_consecutive_overs and player_id == innings.previous_bowler_id:
            raise InvalidBowlerError("The same bowler cannot bowl consecutive overs.")
        bowler = innings.bowlers.setdefault(player_id, BowlerState(player_id=player_id))
        if bowler.legal_balls >= next_state.rules.bowler_max_legal_balls:
            raise InvalidBowlerError("This bowler has reached the over limit.")
        innings.current_bowler_id = player_id
        innings.needs_new_bowler = False
        innings.current_over = []
        bowler.current_over_conceded = 0
        return EngineResult(
            next_state,
            [DomainEvent(ScoringEventType.BOWLER_SELECTED, {"player_id": str(player_id)})],
        )

    def retire(self, state: MatchState, command: RetireCommand) -> EngineResult:
        next_state = deepcopy(state)
        innings = self._require_live_innings(next_state)
        if innings.needs_new_batter:
            raise BatterSelectionRequiredError()
        player_id = command.player_id
        if player_id not in {innings.striker_id, innings.non_striker_id}:
            raise InvalidNextBatterError("Only a batter at the crease can retire.")
        batter = innings.batters[player_id]
        if player_id == innings.striker_id:
            innings.striker_id = None
            innings.vacant_end = "striker"
        else:
            innings.non_striker_id = None
            innings.vacant_end = "non_striker"
        innings.current_partnership = None
        events: list[DomainEvent]
        if command.hurt:
            batter.is_retired_hurt = True
            innings.needs_new_batter = True
            events = [
                DomainEvent(
                    ScoringEventType.BATTER_RETIRED,
                    {"player_id": str(player_id), "hurt": True},
                )
            ]
        else:
            batter.is_out = True
            batter.is_retired_out = True
            batter.dismissal_type = DismissalType.RETIRED_OUT
            innings.wickets += 1
            innings.fall_of_wickets.append(
                FallOfWicket(
                    wicket_number=innings.wickets,
                    team_score=innings.total_runs,
                    player_id=player_id,
                    legal_balls=innings.legal_balls,
                )
            )
            innings.needs_new_batter = innings.wickets < next_state.rules.maximum_wickets
            events = [
                DomainEvent(
                    ScoringEventType.BATTER_RETIRED,
                    {"player_id": str(player_id), "hurt": False},
                )
            ]
            events.extend(self._complete_if_needed(next_state, innings))
        return EngineResult(next_state, events)

    def _require_live_innings(self, state: MatchState) -> InningsState:
        if state.status == MatchPlayStatus.COMPLETED:
            raise MatchCompleteError()
        innings = state.current_innings
        if innings is None or innings.status != InningsStatus.LIVE:
            raise InningsCompleteError()
        return innings

    def _validate_openers(
        self,
        batting_ids: tuple[UUID, ...],
        bowling_ids: tuple[UUID, ...],
        striker_id: UUID,
        non_striker_id: UUID,
        bowler_id: UUID,
    ) -> None:
        if striker_id == non_striker_id:
            raise InvalidNextBatterError("Striker and non-striker must be different.")
        if striker_id not in batting_ids or non_striker_id not in batting_ids:
            raise InvalidNextBatterError("Opening batters must belong to the batting Playing XI.")
        if bowler_id not in bowling_ids:
            raise InvalidBowlerError("Bowler must belong to the bowling Playing XI.")

    def _validate_dismissal_players(
        self,
        command: DeliveryCommand,
        striker_id: UUID,
        non_striker_id: UUID,
        innings: InningsState,
    ) -> None:
        dismissal = command.dismissal
        if dismissal is None:
            return
        crease = {striker_id, non_striker_id}
        if dismissal.dismissed_player_id not in crease:
            raise InvalidDismissalError("Dismissed batter must be at the crease.")
        if dismissal.type in STRIKER_ONLY_DISMISSALS and dismissal.dismissed_player_id != striker_id:
            raise InvalidDismissalError(f"{dismissal.type} can only dismiss the striker.")
        if dismissal.fielder_id is not None and dismissal.fielder_id not in innings.bowling_player_ids:
            raise InvalidDismissalError("Fielder must belong to the bowling Playing XI.")

    def _swap_ends(self, innings: InningsState) -> None:
        innings.striker_id, innings.non_striker_id = innings.non_striker_id, innings.striker_id
        if innings.vacant_end == "striker":
            innings.vacant_end = "non_striker"
        elif innings.vacant_end == "non_striker":
            innings.vacant_end = "striker"

    def _apply_wicket(
        self,
        state: MatchState,
        innings: InningsState,
        dismissal_type: DismissalType,
        dismissed_id: UUID,
    ) -> None:
        batter = innings.batters[dismissed_id]
        batter.is_out = True
        batter.dismissal_type = dismissal_type
        if dismissed_id == innings.striker_id:
            innings.striker_id = None
            innings.vacant_end = "striker"
        elif dismissed_id == innings.non_striker_id:
            innings.non_striker_id = None
            innings.vacant_end = "non_striker"
        else:
            raise InvalidDismissalError("Dismissed batter is not at the crease after running.")
        innings.wickets += 1
        innings.fall_of_wickets.append(
            FallOfWicket(
                wicket_number=innings.wickets,
                team_score=innings.total_runs,
                player_id=dismissed_id,
                legal_balls=innings.legal_balls,
            )
        )
        innings.current_partnership = None
        if state.rules.bowler_credited(dismissal_type) and innings.current_bowler_id is not None:
            innings.bowlers[innings.current_bowler_id].wickets += 1
        innings.needs_new_batter = innings.wickets < state.rules.maximum_wickets

    def _innings_should_complete(self, state: MatchState, innings: InningsState) -> bool:
        return (
            innings.wickets >= state.rules.maximum_wickets
            or innings.legal_balls >= state.rules.maximum_legal_balls
            or (innings.target_runs is not None and innings.total_runs >= innings.target_runs)
        )

    def _complete_if_needed(self, state: MatchState, innings: InningsState) -> list[DomainEvent]:
        if not self._innings_should_complete(state, innings):
            return []
        innings.status = InningsStatus.COMPLETED
        innings.needs_new_batter = False
        innings.needs_new_bowler = False
        events = [DomainEvent(ScoringEventType.INNINGS_COMPLETED, {"innings_number": innings.innings_number})]
        if innings.innings_number >= 2:
            events.append(self._complete_match(state, innings))
        return events

    def _complete_match(self, state: MatchState, second: InningsState) -> DomainEvent:
        first = next(item for item in state.innings if item.innings_number == 1)
        state.status = MatchPlayStatus.COMPLETED
        if second.total_runs >= (second.target_runs or first.total_runs + 1):
            state.result_type = ResultType.WON
            state.winner_team_id = second.batting_team_id
            state.margin_wickets = state.rules.maximum_wickets - second.wickets
            state.margin_runs = None
        elif second.total_runs == first.total_runs:
            state.result_type = ResultType.TIED
            state.winner_team_id = None
            state.margin_runs = None
            state.margin_wickets = None
        else:
            state.result_type = ResultType.WON
            state.winner_team_id = first.batting_team_id
            state.margin_runs = first.total_runs - second.total_runs
            state.margin_wickets = None
        return DomainEvent(
            ScoringEventType.MATCH_COMPLETED,
            {
                "result_type": state.result_type.value if state.result_type else None,
                "winner_team_id": str(state.winner_team_id) if state.winner_team_id else None,
                "margin_runs": state.margin_runs,
                "margin_wickets": state.margin_wickets,
            },
        )


def new_match_state(
    *,
    match_id: UUID,
    rules: MatchRules,
    batting_first_team_id: UUID,
    bowling_first_team_id: UUID,
) -> MatchState:
    return MatchState(
        match_id=match_id,
        rules=rules,
        batting_first_team_id=batting_first_team_id,
        bowling_first_team_id=bowling_first_team_id,
    )
