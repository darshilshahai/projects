from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from app.cricket.types import DismissalType


@dataclass(frozen=True)
class MatchRules:
    overs_per_innings: int
    balls_per_over: int
    players_per_team: int
    format: str = "CUSTOM"
    innings_per_team: int = 1
    enforce_consecutive_overs: bool = True
    penalty_runs_charged_to_bowler: bool = False

    @property
    def maximum_wickets(self) -> int:
        return self.players_per_team - 1

    @property
    def maximum_legal_balls(self) -> int:
        return self.overs_per_innings * self.balls_per_over

    @property
    def bowler_max_overs(self) -> int:
        return max(1, ceil(self.overs_per_innings / 5))

    @property
    def bowler_max_legal_balls(self) -> int:
        return self.bowler_max_overs * self.balls_per_over

    def bowler_credited(self, dismissal: DismissalType) -> bool:
        from app.cricket.types import BOWLER_CREDITED_DISMISSALS

        return dismissal in BOWLER_CREDITED_DISMISSALS

    @classmethod
    def from_match(
        cls,
        *,
        overs_per_innings: int,
        balls_per_over: int,
        players_per_team: int,
        format: str,
    ) -> MatchRules:
        return cls(
            overs_per_innings=overs_per_innings,
            balls_per_over=balls_per_over,
            players_per_team=players_per_team,
            format=format,
        )
