"""Deterministic turning-point candidates.

Thresholds are analytical heuristics, not official cricket laws.

- Wicket cluster: 2+ wickets within 12 legal balls
- Collapse: 3 wickets for <= 20 runs in a consecutive FoW sequence
- High-scoring / wicket overs: top 3 by runs / wickets (format-agnostic)
- Large partnerships: top 3 by runs
- Chase acceleration / stall: last 30% RR vs earlier RR (second innings only)
"""

from __future__ import annotations

from dataclasses import dataclass

from app.cricket.formatters import run_rate, scorecard_rate
from app.schemas.scorecard import FallOfWicketRow, OverSummaryRow, PartnershipRow

WICKET_CLUSTER_MIN_WICKETS = 2
WICKET_CLUSTER_LEGAL_BALLS = 12
COLLAPSE_WICKETS = 3
COLLAPSE_MAX_RUNS = 20
TOP_OVER_LIMIT = 3
TOP_PARTNERSHIP_LIMIT = 3
CHASE_RR_DELTA = 1.5


@dataclass(frozen=True)
class KeyEventCandidate:
    event_type: str
    label: str
    summary: str
    innings_number: int
    values: dict[str, int | float | str]
    over_number: int | None = None


def detect_key_events(
    *,
    innings_number: int,
    overs: list[OverSummaryRow],
    fall_of_wickets: list[FallOfWicketRow],
    partnerships: list[PartnershipRow],
    balls_per_over: int,
    target: int | None,
) -> list[KeyEventCandidate]:
    events: list[KeyEventCandidate] = []
    events.extend(_wicket_clusters(innings_number, fall_of_wickets))
    events.extend(_collapses(innings_number, fall_of_wickets))
    events.extend(_top_scoring_overs(innings_number, overs))
    events.extend(_top_wicket_overs(innings_number, overs))
    events.extend(_large_partnerships(innings_number, partnerships))
    events.extend(_chase_swings(innings_number, overs, balls_per_over, target))
    return events


def _wicket_clusters(innings_number: int, fall_of_wickets: list[FallOfWicketRow]) -> list[KeyEventCandidate]:
    events: list[KeyEventCandidate] = []
    seen: set[tuple[int, int]] = set()
    for index, start in enumerate(fall_of_wickets):
        cluster = [start]
        for nxt in fall_of_wickets[index + 1 :]:
            if nxt.legal_balls - start.legal_balls <= WICKET_CLUSTER_LEGAL_BALLS:
                cluster.append(nxt)
            else:
                break
        if len(cluster) < WICKET_CLUSTER_MIN_WICKETS:
            continue
        key = (cluster[0].wicket_number, cluster[-1].wicket_number)
        if key in seen:
            continue
        seen.add(key)
        events.append(
            KeyEventCandidate(
                event_type="WICKET_CLUSTER",
                label=f"Wickets {cluster[0].wicket_number}-{cluster[-1].wicket_number}",
                summary=(
                    f"{len(cluster)} wickets fell within {WICKET_CLUSTER_LEGAL_BALLS} legal balls "
                    f"({cluster[0].overs} to {cluster[-1].overs}), score {cluster[0].score} to {cluster[-1].score}."
                ),
                innings_number=innings_number,
                values={
                    "wickets": len(cluster),
                    "from_score": cluster[0].score,
                    "to_score": cluster[-1].score,
                    "from_over": cluster[0].overs,
                    "to_over": cluster[-1].overs,
                },
            )
        )
    return events


def _collapses(innings_number: int, fall_of_wickets: list[FallOfWicketRow]) -> list[KeyEventCandidate]:
    events: list[KeyEventCandidate] = []
    for index in range(0, len(fall_of_wickets) - COLLAPSE_WICKETS + 1):
        window = fall_of_wickets[index : index + COLLAPSE_WICKETS]
        previous_score = 0 if index == 0 else fall_of_wickets[index - 1].score
        runs = window[-1].score - previous_score
        if runs > COLLAPSE_MAX_RUNS:
            continue
        events.append(
            KeyEventCandidate(
                event_type="COLLAPSE",
                label=f"Collapse wickets {window[0].wicket_number}-{window[-1].wicket_number}",
                summary=(f"{COLLAPSE_WICKETS} wickets fell for {runs} runs ({window[0].overs} to {window[-1].overs})."),
                innings_number=innings_number,
                values={
                    "wickets": COLLAPSE_WICKETS,
                    "runs": runs,
                    "from_over": window[0].overs,
                    "to_over": window[-1].overs,
                },
            )
        )
    return events


def _top_scoring_overs(innings_number: int, overs: list[OverSummaryRow]) -> list[KeyEventCandidate]:
    ranked = sorted((item for item in overs if item.runs > 0), key=lambda item: (-item.runs, item.over_number))
    events: list[KeyEventCandidate] = []
    for item in ranked[:TOP_OVER_LIMIT]:
        events.append(
            KeyEventCandidate(
                event_type="HIGH_SCORING_OVER",
                label=f"Over {item.over_number}",
                summary=f"Over {item.over_number} produced {item.runs} runs and {item.wickets} wickets.",
                innings_number=innings_number,
                over_number=item.over_number,
                values={"over": item.over_number, "runs": item.runs, "wickets": item.wickets},
            )
        )
    return events


def _top_wicket_overs(innings_number: int, overs: list[OverSummaryRow]) -> list[KeyEventCandidate]:
    ranked = sorted(
        (item for item in overs if item.wickets > 0),
        key=lambda item: (-item.wickets, -item.runs, item.over_number),
    )
    events: list[KeyEventCandidate] = []
    for item in ranked[:TOP_OVER_LIMIT]:
        events.append(
            KeyEventCandidate(
                event_type="WICKET_OVER",
                label=f"Over {item.over_number}",
                summary=f"Over {item.over_number} took {item.wickets} wickets for {item.runs} runs.",
                innings_number=innings_number,
                over_number=item.over_number,
                values={"over": item.over_number, "runs": item.runs, "wickets": item.wickets},
            )
        )
    return events


def _large_partnerships(innings_number: int, partnerships: list[PartnershipRow]) -> list[KeyEventCandidate]:
    ranked = sorted((item for item in partnerships if item.runs > 0), key=lambda item: (-item.runs, item.start_score))
    events: list[KeyEventCandidate] = []
    for item in ranked[:TOP_PARTNERSHIP_LIMIT]:
        events.append(
            KeyEventCandidate(
                event_type="LARGE_PARTNERSHIP",
                label=f"{item.batter_1_name} / {item.batter_2_name}",
                summary=(
                    f"{item.batter_1_name} and {item.batter_2_name} added {item.runs} runs "
                    f"from {item.legal_balls} legal balls."
                ),
                innings_number=innings_number,
                values={
                    "runs": item.runs,
                    "legal_balls": item.legal_balls,
                    "start_score": item.start_score,
                    "end_score": item.end_score,
                },
            )
        )
    return events


def _chase_swings(
    innings_number: int,
    overs: list[OverSummaryRow],
    balls_per_over: int,
    target: int | None,
) -> list[KeyEventCandidate]:
    if target is None or innings_number < 2 or len(overs) < 2:
        return []
    split = max(1, round(len(overs) * 0.70))
    early = overs[:split]
    late = overs[split:]
    if not late:
        return []
    early_runs = sum(item.runs for item in early)
    early_balls = sum(item.legal_balls for item in early)
    late_runs = sum(item.runs for item in late)
    late_balls = sum(item.legal_balls for item in late)
    early_rr = scorecard_rate(run_rate(early_runs, early_balls, balls_per_over))
    late_rr = scorecard_rate(run_rate(late_runs, late_balls, balls_per_over))
    late_wickets = sum(item.wickets for item in late)
    events: list[KeyEventCandidate] = []
    if late_rr >= early_rr + CHASE_RR_DELTA:
        events.append(
            KeyEventCandidate(
                event_type="CHASE_ACCELERATION",
                label="Chase acceleration",
                summary=(
                    f"Required chase accelerated: later overs RR {late_rr} vs earlier RR {early_rr} (target {target})."
                ),
                innings_number=innings_number,
                values={"early_rr": early_rr, "late_rr": late_rr, "target": target, "late_runs": late_runs},
            )
        )
    elif late_rr + CHASE_RR_DELTA <= early_rr:
        events.append(
            KeyEventCandidate(
                event_type="CHASE_STALL",
                label="Chase stall",
                summary=(
                    f"Chase stalled: later overs RR {late_rr} vs earlier RR {early_rr}, "
                    f"{late_wickets} late wickets (target {target})."
                ),
                innings_number=innings_number,
                values={
                    "early_rr": early_rr,
                    "late_rr": late_rr,
                    "target": target,
                    "late_wickets": late_wickets,
                },
            )
        )
    return events
