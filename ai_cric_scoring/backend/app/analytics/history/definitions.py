"""Canonical historical cricket statistics.

Batting average is runs / dismissals, not runs / matches.
Career strike rate is total runs / total balls * 100, not the mean of innings SRs.
Win percentage uses all completed matches including ties as the denominator.
"""

from __future__ import annotations

from app.cricket.formatters import format_overs, round_rate

DISMISSAL_STATUSES = frozenset({"OUT", "RETIRED_OUT"})
NOT_OUT_STATUSES = frozenset({"BATTING", "NOT_OUT", "RETIRED_HURT"})

RECENT_APPEARANCES = 5
LAST_N_MIN = 1
LAST_N_MAX = 50

MIN_DISMISSALS_FOR_AVERAGE_RANKING = 3
MIN_BALLS_FOR_STRIKE_RATE_RANKING = 12
MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING = 12


def clamp_last_n(value: int | None) -> int | None:
    if value is None:
        return None
    return max(LAST_N_MIN, min(LAST_N_MAX, value))


def is_dismissal(status: str) -> bool:
    return status in DISMISSAL_STATUSES


def is_not_out(status: str) -> bool:
    return not is_dismissal(status)


def batting_average(runs: int, dismissals: int) -> float | None:
    if dismissals <= 0:
        return None
    return round_rate(runs / dismissals)


def batting_strike_rate(runs: int, balls: int) -> float | None:
    if balls <= 0:
        return None
    return round_rate(runs / balls * 100)


def bowling_average(runs_conceded: int, wickets: int) -> float | None:
    if wickets <= 0:
        return None
    return round_rate(runs_conceded / wickets)


def bowling_economy(
    runs_conceded: int,
    legal_balls: int,
    balls_per_over: int | None,
    *,
    mixed_rules: bool,
) -> float | None:
    if mixed_rules or balls_per_over is None or legal_balls <= 0:
        return None
    return round_rate(runs_conceded / legal_balls * balls_per_over)


def runs_per_legal_ball(runs_conceded: int, legal_balls: int) -> float | None:
    if legal_balls <= 0:
        return None
    return round_rate(runs_conceded / legal_balls)


def win_percentage(wins: int, completed_matches: int) -> float | None:
    if completed_matches <= 0:
        return None
    return round_rate(wins / completed_matches * 100)


def highest_score_display(runs: int | None, not_out: bool) -> str | None:
    if runs is None:
        return None
    return f"{runs}*" if not_out else str(runs)


def overs_display(legal_balls: int, balls_per_over: int | None, *, mixed_rules: bool) -> str | None:
    if mixed_rules or balls_per_over is None or legal_balls < 0:
        return None
    return format_overs(legal_balls, balls_per_over)


def best_bowling_display(wickets: int, runs_conceded: int) -> str:
    return f"{wickets}/{runs_conceded}"
