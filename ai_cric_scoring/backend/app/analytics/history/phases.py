"""Closing-phase (death-over) aggregation from stored deliveries."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from app.analytics.phases import define_analytical_phases
from app.models.enums import MatchFormat


def aggregate_closing_phase(
    rows: list[tuple[UUID, int, str, int, int]],
) -> dict | None:
    """Aggregate closing-phase runs from (match_id, overs, format, over_number, runs).

    Returns None when any match in the set has no distinct closing phase.
    """
    by_match: dict[UUID, dict] = {}
    for match_id, overs, fmt, over_number, runs in rows:
        bucket = by_match.setdefault(
            match_id,
            {"overs": overs, "format": fmt, "overs_runs": defaultdict(int)},
        )
        bucket["overs_runs"][over_number] += runs

    totals: list[int] = []
    for data in by_match.values():
        try:
            match_format = MatchFormat(data["format"])
        except ValueError:
            return None
        phases = define_analytical_phases(match_format, int(data["overs"]))
        closing = next((item for item in phases if item.key == "closing"), None)
        if closing is None:
            return None
        totals.append(
            sum(
                runs
                for over_number, runs in data["overs_runs"].items()
                if closing.start_over <= over_number <= closing.end_over
            )
        )
    if not totals:
        return None
    return {
        "matches": len(totals),
        "runs": sum(totals),
        "average_runs": round(sum(totals) / len(totals), 2),
    }
