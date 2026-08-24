from __future__ import annotations

from uuid import UUID

from app.analytics.history.definitions import win_percentage
from app.analytics.history.types import TeamCareer, TeamMatchRow
from app.cricket.formatters import round_rate
from app.models.enums import ResultType


def aggregate_team(rows: list[TeamMatchRow]) -> TeamCareer:
    wins = 0
    losses = 0
    ties = 0
    scored: list[int] = []
    conceded: list[int] = []
    chasing = 0
    chasing_wins = 0
    defending = 0
    defending_wins = 0
    recent: list[tuple[object, str]] = []

    for row in rows:
        won = row.winner_match_team_id == row.match_team_id
        tied = row.result_type == ResultType.TIED.value
        if tied:
            ties += 1
            code = "T"
        elif won:
            wins += 1
            code = "W"
        else:
            losses += 1
            code = "L"
        recent.append((row.completed_at or row.match_id, code))
        if row.runs_scored is not None:
            scored.append(row.runs_scored)
        if row.runs_conceded is not None:
            conceded.append(row.runs_conceded)
        if row.batting_innings_number == 2:
            chasing += 1
            if won:
                chasing_wins += 1
        elif row.batting_innings_number == 1:
            defending += 1
            if won:
                defending_wins += 1

    recent.sort(key=lambda item: str(item[0]), reverse=True)
    matches = len(rows)
    return TeamCareer(
        matches=matches,
        wins=wins,
        losses=losses,
        ties=ties,
        win_percentage=win_percentage(wins, matches),
        average_runs_scored=_mean(scored),
        average_runs_conceded=_mean(conceded),
        highest_score=max(scored) if scored else None,
        lowest_completed_score=min(scored) if scored else None,
        matches_chasing=chasing,
        wins_chasing=chasing_wins,
        matches_defending=defending,
        wins_defending=defending_wins,
        recent_results=[code for _, code in recent[:10]],
    )


def _mean(values: list[int]) -> float | None:
    if not values:
        return None
    return round_rate(sum(values) / len(values))


def head_to_head(team_a_id: UUID, team_b_id: UUID, rows_a: list[TeamMatchRow]) -> dict[str, int]:
    matches = [row for row in rows_a if row.opponent_team_id == team_b_id]
    a_wins = 0
    b_wins = 0
    ties = 0
    for row in matches:
        if row.result_type == ResultType.TIED.value:
            ties += 1
        elif row.winner_match_team_id == row.match_team_id:
            a_wins += 1
        elif row.result_type == ResultType.WON.value:
            b_wins += 1
    return {
        "matches": len(matches),
        "team_a_wins": a_wins,
        "team_b_wins": b_wins,
        "ties": ties,
    }
