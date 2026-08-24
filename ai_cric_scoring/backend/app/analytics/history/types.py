from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class BattingInningsRow:
    match_id: UUID
    player_id: UUID
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    status: str
    completed_at: datetime | None = None
    opponent_name: str | None = None
    result_code: str | None = None


@dataclass(frozen=True)
class BowlingInningsRow:
    match_id: UUID
    player_id: UUID
    legal_balls: int
    runs_conceded: int
    wickets: int
    wides: int
    no_balls: int
    maidens: int
    balls_per_over: int
    completed_at: datetime | None = None
    opponent_name: str | None = None
    result_code: str | None = None


@dataclass(frozen=True)
class AppearanceRow:
    match_id: UUID
    player_id: UUID
    team_id: UUID
    completed_at: datetime | None
    format: str
    balls_per_over: int
    opponent_name: str
    result_code: str
    display_name_snapshot: str


@dataclass(frozen=True)
class TeamMatchRow:
    match_id: UUID
    team_id: UUID
    match_team_id: UUID
    completed_at: datetime | None
    format: str
    result_type: str | None
    winner_match_team_id: UUID | None
    batting_innings_number: int | None
    runs_scored: int | None
    wickets_lost: int | None
    runs_conceded: int | None
    opponent_name: str
    opponent_team_id: UUID | None


@dataclass
class BattingCareer:
    matches: int
    innings: int
    runs: int
    balls: int
    not_outs: int
    dismissals: int
    highest_score: int | None
    highest_not_out: bool
    fours: int
    sixes: int
    strike_rate: float | None
    batting_average: float | None


@dataclass
class BowlingCareer:
    matches: int
    innings_bowled: int
    legal_balls: int
    overs_display: str | None
    runs_conceded: int
    wickets: int
    wides: int
    no_balls: int
    maidens: int
    economy: float | None
    bowling_average: float | None
    best_bowling: str | None
    mixed_rules: bool
    runs_per_legal_ball: float | None


@dataclass
class TeamCareer:
    matches: int
    wins: int
    losses: int
    ties: int
    win_percentage: float | None
    average_runs_scored: float | None
    average_runs_conceded: float | None
    highest_score: int | None
    lowest_completed_score: int | None
    matches_chasing: int
    wins_chasing: int
    matches_defending: int
    wins_defending: int
    recent_results: list[str] = field(default_factory=list)


@dataclass
class TrendWindow:
    metric: str
    last_n: float | None
    previous_n: float | None
    delta: float | None
    sample_last: int
    sample_previous: int
