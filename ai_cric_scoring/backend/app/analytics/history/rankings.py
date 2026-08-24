from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.analytics.history.definitions import (
    MIN_BALLS_FOR_STRIKE_RATE_RANKING,
    MIN_DISMISSALS_FOR_AVERAGE_RANKING,
    MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING,
    batting_average,
    batting_strike_rate,
    bowling_average,
    bowling_economy,
)


@dataclass
class RankingCandidate:
    player_id: UUID
    name: str
    runs: int = 0
    balls: int = 0
    dismissals: int = 0
    innings: int = 0
    wickets: int = 0
    runs_conceded: int = 0
    legal_balls: int = 0
    balls_per_over: int | None = None
    mixed_rules: bool = False


def ranking_value(metric: str, candidate: RankingCandidate) -> float | None:
    if metric == "runs":
        return float(candidate.runs)
    if metric == "wickets":
        return float(candidate.wickets)
    if metric == "batting_average":
        if candidate.dismissals < MIN_DISMISSALS_FOR_AVERAGE_RANKING:
            return None
        return batting_average(candidate.runs, candidate.dismissals)
    if metric == "strike_rate":
        if candidate.balls < MIN_BALLS_FOR_STRIKE_RATE_RANKING:
            return None
        return batting_strike_rate(candidate.runs, candidate.balls)
    if metric == "economy":
        if candidate.legal_balls < MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING or candidate.mixed_rules:
            return None
        return bowling_economy(
            candidate.runs_conceded,
            candidate.legal_balls,
            candidate.balls_per_over,
            mixed_rules=candidate.mixed_rules,
        )
    if metric == "bowling_average":
        return bowling_average(candidate.runs_conceded, candidate.wickets)
    return None


def sort_leaderboard(metric: str, candidates: list[RankingCandidate]) -> list[tuple[RankingCandidate, float]]:
    scored: list[tuple[RankingCandidate, float]] = []
    for item in candidates:
        value = ranking_value(metric, item)
        if value is None:
            continue
        scored.append((item, value))
    reverse = metric != "economy"
    scored.sort(key=lambda pair: pair[1], reverse=reverse)
    return scored
