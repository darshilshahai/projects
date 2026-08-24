from __future__ import annotations

from app.analytics.history.definitions import highest_score_display, is_not_out
from app.analytics.history.types import BattingInningsRow, BowlingInningsRow


def batting_form_entries(rows: list[BattingInningsRow], *, last_n: int) -> list[dict]:
    ordered = sorted(rows, key=lambda item: item.completed_at or item.match_id, reverse=True)
    entries = []
    for item in ordered[:last_n]:
        not_out = is_not_out(item.status)
        entries.append(
            {
                "match_id": item.match_id,
                "completed_at": item.completed_at,
                "opponent_name": item.opponent_name,
                "runs": item.runs,
                "not_out": not_out,
                "display": highest_score_display(item.runs, not_out),
                "result": item.result_code,
            }
        )
    return entries


def bowling_form_entries(rows: list[BowlingInningsRow], *, last_n: int) -> list[dict]:
    ordered = sorted(rows, key=lambda item: item.completed_at or item.match_id, reverse=True)
    entries = []
    for item in ordered[:last_n]:
        entries.append(
            {
                "match_id": item.match_id,
                "completed_at": item.completed_at,
                "opponent_name": item.opponent_name,
                "wickets": item.wickets,
                "runs_conceded": item.runs_conceded,
                "display": f"{item.wickets}/{item.runs_conceded}",
                "result": item.result_code,
            }
        )
    return entries
