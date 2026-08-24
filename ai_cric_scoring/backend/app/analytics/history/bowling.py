from __future__ import annotations

from app.analytics.history.definitions import (
    best_bowling_display,
    bowling_average,
    bowling_economy,
    overs_display,
    runs_per_legal_ball,
)
from app.analytics.history.types import BowlingCareer, BowlingInningsRow


def aggregate_bowling(rows: list[BowlingInningsRow], *, matches_played: int) -> BowlingCareer:
    innings = len(rows)
    legal_balls = sum(item.legal_balls for item in rows)
    runs_conceded = sum(item.runs_conceded for item in rows)
    wickets = sum(item.wickets for item in rows)
    wides = sum(item.wides for item in rows)
    no_balls = sum(item.no_balls for item in rows)
    maidens = sum(item.maidens for item in rows)
    bpo_values = {item.balls_per_over for item in rows}
    mixed = len(bpo_values) > 1
    balls_per_over = next(iter(bpo_values)) if len(bpo_values) == 1 else None
    best = _best_spell(rows)
    return BowlingCareer(
        matches=matches_played,
        innings_bowled=innings,
        legal_balls=legal_balls,
        overs_display=overs_display(legal_balls, balls_per_over, mixed_rules=mixed),
        runs_conceded=runs_conceded,
        wickets=wickets,
        wides=wides,
        no_balls=no_balls,
        maidens=maidens,
        economy=bowling_economy(runs_conceded, legal_balls, balls_per_over, mixed_rules=mixed),
        bowling_average=bowling_average(runs_conceded, wickets),
        best_bowling=best,
        mixed_rules=mixed,
        runs_per_legal_ball=runs_per_legal_ball(runs_conceded, legal_balls),
    )


def _best_spell(rows: list[BowlingInningsRow]) -> str | None:
    if not rows:
        return None
    best = max(rows, key=lambda item: (item.wickets, -item.runs_conceded))
    return best_bowling_display(best.wickets, best.runs_conceded)
