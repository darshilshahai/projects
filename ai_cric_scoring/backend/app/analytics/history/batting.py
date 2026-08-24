from __future__ import annotations

from app.analytics.history.definitions import (
    batting_average,
    batting_strike_rate,
    is_dismissal,
    is_not_out,
)
from app.analytics.history.types import BattingCareer, BattingInningsRow


def aggregate_batting(rows: list[BattingInningsRow], *, matches_played: int) -> BattingCareer:
    innings = len(rows)
    runs = sum(item.runs for item in rows)
    balls = sum(item.balls_faced for item in rows)
    fours = sum(item.fours for item in rows)
    sixes = sum(item.sixes for item in rows)
    dismissals = sum(1 for item in rows if is_dismissal(item.status))
    not_outs = sum(1 for item in rows if is_not_out(item.status))
    highest: BattingInningsRow | None = None
    if rows:
        highest = max(rows, key=lambda item: (item.runs, 1 if is_not_out(item.status) else 0))
    return BattingCareer(
        matches=matches_played,
        innings=innings,
        runs=runs,
        balls=balls,
        not_outs=not_outs,
        dismissals=dismissals,
        highest_score=highest.runs if highest else None,
        highest_not_out=bool(highest and is_not_out(highest.status)),
        fours=fours,
        sixes=sixes,
        strike_rate=batting_strike_rate(runs, balls),
        batting_average=batting_average(runs, dismissals),
    )
