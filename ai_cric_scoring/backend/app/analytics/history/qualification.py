"""Leaderboard qualification thresholds.

Detail screens still show raw sample size; these gates apply to rankings only.
"""

from app.analytics.history.definitions import (
    MIN_BALLS_FOR_STRIKE_RATE_RANKING,
    MIN_DISMISSALS_FOR_AVERAGE_RANKING,
    MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING,
)

__all__ = [
    "MIN_BALLS_FOR_STRIKE_RATE_RANKING",
    "MIN_DISMISSALS_FOR_AVERAGE_RANKING",
    "MIN_LEGAL_BALLS_FOR_ECONOMY_RANKING",
]
