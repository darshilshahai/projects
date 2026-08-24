"""Copy notes for comparison responses. Stats themselves come from batting/bowling/team aggregations."""

from app.analytics.history.filters import HistoricalScope


def last_n_compare_note(scope: HistoricalScope) -> str | None:
    if scope.last_n is None:
        return None
    return f"Each player's most recent {scope.last_n} appearances."
