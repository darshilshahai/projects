"""Analytical innings-phase segmentation.

These ranges are application-level analysis segments, not official playing
conditions. Do not present them as competition Powerplay rules unless the
match format is a standard T20/ODI length and the label is marked analytical.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.cricket.formatters import run_rate, scorecard_rate
from app.models.enums import MatchFormat
from app.schemas.scorecard import OverSummaryRow


@dataclass(frozen=True)
class PhaseDefinition:
    key: str
    label: str
    start_over: int
    end_over: int


@dataclass(frozen=True)
class PhaseStats:
    key: str
    label: str
    start_over: int
    end_over: int
    runs: int
    wickets: int
    legal_balls: int
    run_rate: float
    boundaries: int
    dots: int


def define_analytical_phases(match_format: MatchFormat, overs_per_innings: int) -> list[PhaseDefinition]:
    """Return 1-based inclusive over ranges for analytical phases."""
    if overs_per_innings <= 0:
        return []
    if match_format is MatchFormat.T20 and overs_per_innings == 20:
        return [
            PhaseDefinition("opening", "Powerplay (analytical)", 1, 6),
            PhaseDefinition("middle", "Middle Overs (analytical)", 7, 15),
            PhaseDefinition("closing", "Death Overs (analytical)", 16, 20),
        ]
    if match_format is MatchFormat.ODI and overs_per_innings == 50:
        return [
            PhaseDefinition("opening", "Opening Phase (analytical)", 1, 10),
            PhaseDefinition("middle", "Middle Phase (analytical)", 11, 40),
            PhaseDefinition("closing", "Closing Phase (analytical)", 41, 50),
        ]
    if match_format is MatchFormat.T10 and overs_per_innings == 10:
        return [
            PhaseDefinition("opening", "Opening Phase (analytical)", 1, 3),
            PhaseDefinition("middle", "Middle Phase (analytical)", 4, 7),
            PhaseDefinition("closing", "Closing Phase (analytical)", 8, 10),
        ]
    return _proportional_phases(overs_per_innings)


def _proportional_phases(overs_per_innings: int) -> list[PhaseDefinition]:
    """Custom / non-standard lengths: first 30% / middle 40% / last 30%.

    Labels are Opening / Middle / Closing Phase — never official Powerplay.
    """
    opening_end = max(1, round(overs_per_innings * 0.30))
    closing_len = max(1, round(overs_per_innings * 0.30))
    closing_start = overs_per_innings - closing_len + 1
    if closing_start <= opening_end:
        return [PhaseDefinition("opening", "Opening Phase (analytical)", 1, overs_per_innings)]
    phases = [PhaseDefinition("opening", "Opening Phase (analytical)", 1, opening_end)]
    middle_start = opening_end + 1
    middle_end = closing_start - 1
    if middle_end >= middle_start:
        phases.append(PhaseDefinition("middle", "Middle Phase (analytical)", middle_start, middle_end))
    phases.append(PhaseDefinition("closing", "Closing Phase (analytical)", closing_start, overs_per_innings))
    return phases


def summarize_phases(
    overs: list[OverSummaryRow],
    *,
    match_format: MatchFormat,
    overs_per_innings: int,
    balls_per_over: int,
) -> list[PhaseStats]:
    stats: list[PhaseStats] = []
    for definition in define_analytical_phases(match_format, overs_per_innings):
        selected = [item for item in overs if definition.start_over <= item.over_number <= definition.end_over]
        if not selected:
            continue
        runs = sum(item.runs for item in selected)
        wickets = sum(item.wickets for item in selected)
        legal_balls = sum(item.legal_balls for item in selected)
        boundaries = 0
        dots = 0
        for over in selected:
            for delivery in over.deliveries:
                if delivery.label in {"4", "6"}:
                    boundaries += 1
                if delivery.label == ".":
                    dots += 1
        stats.append(
            PhaseStats(
                key=definition.key,
                label=definition.label,
                start_over=definition.start_over,
                end_over=definition.end_over,
                runs=runs,
                wickets=wickets,
                legal_balls=legal_balls,
                run_rate=scorecard_rate(run_rate(runs, legal_balls, balls_per_over)),
                boundaries=boundaries,
                dots=dots,
            )
        )
    return stats
