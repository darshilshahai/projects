from __future__ import annotations

from app.cricket.types import BatterStatus, DismissalType


def format_dismissal(
    *,
    status: str,
    dismissal_type: str | None,
    bowler_name: str | None = None,
    fielder_name: str | None = None,
) -> str:
    if status == BatterStatus.RETIRED_HURT.value:
        return "retired hurt"
    if status == BatterStatus.RETIRED_OUT.value or dismissal_type == DismissalType.RETIRED_OUT.value:
        return "retired out"
    if status in {BatterStatus.BATTING.value, BatterStatus.NOT_OUT.value} or not dismissal_type:
        return "not out"

    bowler = bowler_name or "unknown"
    fielder = fielder_name
    kind = DismissalType(dismissal_type)
    if kind is DismissalType.BOWLED:
        return f"b {bowler}"
    if kind is DismissalType.CAUGHT:
        return f"c {fielder or 'unknown'} b {bowler}"
    if kind is DismissalType.LBW:
        return f"lbw b {bowler}"
    if kind is DismissalType.STUMPED:
        return f"st {fielder or 'unknown'} b {bowler}"
    if kind is DismissalType.RUN_OUT:
        return f"run out ({fielder})" if fielder else "run out"
    if kind is DismissalType.HIT_WICKET:
        return f"hit wicket b {bowler}"
    if kind is DismissalType.OBSTRUCTING_THE_FIELD:
        return "obstructing the field"
    if kind is DismissalType.HIT_THE_BALL_TWICE:
        return "hit the ball twice"
    return kind.value.replace("_", " ").lower()
