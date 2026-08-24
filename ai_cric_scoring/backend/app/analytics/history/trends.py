from __future__ import annotations

from app.analytics.history.batting import aggregate_batting
from app.analytics.history.bowling import aggregate_bowling
from app.analytics.history.definitions import RECENT_APPEARANCES
from app.analytics.history.teams import aggregate_team
from app.analytics.history.types import BattingInningsRow, BowlingInningsRow, TeamMatchRow, TrendWindow
from app.cricket.formatters import round_rate


def split_windows(rows: list, *, window: int = RECENT_APPEARANCES) -> tuple[list, list]:
    ordered = sorted(rows, key=lambda item: getattr(item, "completed_at", None) or item.match_id, reverse=True)
    return ordered[:window], ordered[window : window * 2]


def batting_trend(rows: list[BattingInningsRow], *, window: int = RECENT_APPEARANCES) -> list[TrendWindow]:
    current_rows, previous_rows = split_windows(rows, window=window)
    current = aggregate_batting(current_rows, matches_played=len({item.match_id for item in current_rows}))
    previous = aggregate_batting(previous_rows, matches_played=len({item.match_id for item in previous_rows}))
    return [
        _delta(
            "batting_average", current.batting_average, previous.batting_average, len(current_rows), len(previous_rows)
        ),
        _delta("strike_rate", current.strike_rate, previous.strike_rate, len(current_rows), len(previous_rows)),
        _delta("runs", float(current.runs), float(previous.runs), len(current_rows), len(previous_rows)),
    ]


def bowling_trend(rows: list[BowlingInningsRow], *, window: int = RECENT_APPEARANCES) -> list[TrendWindow]:
    current_rows, previous_rows = split_windows(rows, window=window)
    current = aggregate_bowling(current_rows, matches_played=len({item.match_id for item in current_rows}))
    previous = aggregate_bowling(previous_rows, matches_played=len({item.match_id for item in previous_rows}))
    return [
        _delta("wickets", float(current.wickets), float(previous.wickets), len(current_rows), len(previous_rows)),
        _delta("economy", current.economy, previous.economy, len(current_rows), len(previous_rows)),
        _delta(
            "bowling_average", current.bowling_average, previous.bowling_average, len(current_rows), len(previous_rows)
        ),
    ]


def team_trend(rows: list[TeamMatchRow], *, window: int = RECENT_APPEARANCES) -> list[TrendWindow]:
    ordered = sorted(rows, key=lambda item: item.completed_at or item.match_id, reverse=True)
    current = aggregate_team(ordered[:window])
    previous = aggregate_team(ordered[window : window * 2])
    return [
        _delta("wins", float(current.wins), float(previous.wins), current.matches, previous.matches),
        _delta("win_percentage", current.win_percentage, previous.win_percentage, current.matches, previous.matches),
        _delta(
            "average_runs_scored",
            current.average_runs_scored,
            previous.average_runs_scored,
            current.matches,
            previous.matches,
        ),
    ]


def _delta(
    metric: str,
    last_n: float | None,
    previous_n: float | None,
    sample_last: int,
    sample_previous: int,
) -> TrendWindow:
    delta = None
    if last_n is not None and previous_n is not None:
        delta = round_rate(last_n - previous_n)
    return TrendWindow(
        metric=metric,
        last_n=last_n,
        previous_n=previous_n,
        delta=delta,
        sample_last=sample_last,
        sample_previous=sample_previous,
    )
