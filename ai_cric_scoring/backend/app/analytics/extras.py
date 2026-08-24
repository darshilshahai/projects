from __future__ import annotations

from collections.abc import Sequence

from app.analytics.types import DeliveryFact, ExtrasBreakdown


def calculate_extras(deliveries: Sequence[DeliveryFact]) -> ExtrasBreakdown:
    return ExtrasBreakdown(
        wides=sum(item.wides for item in deliveries),
        no_balls=sum(item.no_balls for item in deliveries),
        byes=sum(item.byes for item in deliveries),
        leg_byes=sum(item.leg_byes for item in deliveries),
        penalty_runs=sum(item.penalty_runs for item in deliveries),
    )
