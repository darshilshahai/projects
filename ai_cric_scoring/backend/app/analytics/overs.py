from __future__ import annotations

from collections.abc import Sequence

from app.analytics.types import DeliveryFact, OverDeliveryFact, OverSummaryFact
from app.cricket.formatters import over_label


def build_over_summaries(
    deliveries: Sequence[DeliveryFact],
    *,
    balls_per_over: int,
) -> list[OverSummaryFact]:
    grouped: dict[int, list[DeliveryFact]] = {}
    for item in deliveries:
        grouped.setdefault(item.over_number, []).append(item)

    summaries: list[OverSummaryFact] = []
    for over_number in sorted(grouped):
        balls = grouped[over_number]
        legal_balls = sum(1 for item in balls if item.is_legal)
        summaries.append(
            OverSummaryFact(
                over_number=over_number,
                runs=sum(item.team_runs for item in balls),
                wickets=sum(1 for item in balls if item.is_team_wicket),
                legal_balls=legal_balls,
                is_complete=legal_balls >= balls_per_over,
                deliveries=tuple(
                    OverDeliveryFact(
                        label=over_label(
                            runs_off_bat=item.runs_off_bat,
                            wides=item.wides,
                            no_balls=item.no_balls,
                            byes=item.byes,
                            leg_byes=item.leg_byes,
                            penalty_runs=item.penalty_runs,
                            wicket=item.is_team_wicket,
                            team_runs=item.team_runs,
                        ),
                        runs=item.team_runs,
                        wicket=item.is_team_wicket,
                        legal=item.is_legal,
                    )
                    for item in balls
                ),
            )
        )
    return summaries
