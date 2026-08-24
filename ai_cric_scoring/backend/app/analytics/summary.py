from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.analytics.types import MatchSummaryFacts, NamedStat, PartnershipFact


@dataclass(frozen=True)
class BatterSummaryInput:
    match_player_id: UUID
    name: str
    runs: int
    fours: int
    sixes: int


@dataclass(frozen=True)
class BowlerSummaryInput:
    match_player_id: UUID
    name: str
    wickets: int
    runs_conceded: int


def build_match_summary(
    *,
    batting: Sequence[BatterSummaryInput],
    bowling: Sequence[BowlerSummaryInput],
    partnerships: Sequence[tuple[PartnershipFact, str]],
    extras_total: int,
) -> MatchSummaryFacts:
    max_runs = max((item.runs for item in batting), default=0)
    highest = tuple(
        NamedStat(match_player_id=item.match_player_id, name=item.name, value=item.runs)
        for item in batting
        if item.runs == max_runs and max_runs > 0
    )
    max_wickets = max((item.wickets for item in bowling), default=0)
    tied = [item for item in bowling if item.wickets == max_wickets and max_wickets > 0]
    tied.sort(key=lambda item: (item.runs_conceded, item.name))
    most_wickets = tuple(
        NamedStat(match_player_id=item.match_player_id, name=item.name, value=item.wickets) for item in tied
    )
    max_stand = max((item.runs for item, _label in partnerships), default=0)
    largest = tuple(
        NamedStat(match_player_id=item.batter_1_id, name=label, value=item.runs)
        for item, label in partnerships
        if item.runs == max_stand and max_stand > 0
    )
    return MatchSummaryFacts(
        highest_scorers=highest,
        most_wickets=most_wickets,
        total_boundaries=sum(item.fours + item.sixes for item in batting),
        total_sixes=sum(item.sixes for item in batting),
        total_extras=extras_total,
        largest_partnerships=largest,
    )
