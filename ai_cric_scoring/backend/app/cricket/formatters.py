from __future__ import annotations

from app.cricket.types import ResultType


def format_overs(legal_balls: int, balls_per_over: int) -> str:
    completed, remainder = divmod(legal_balls, balls_per_over)
    return f"{completed}.{remainder}"


def format_result(
    *,
    result_type: ResultType | None,
    winner_name: str | None,
    margin_runs: int | None,
    margin_wickets: int | None,
) -> str | None:
    if result_type is ResultType.TIED:
        return "Match tied"
    if result_type is None or winner_name is None:
        return None
    if margin_wickets is not None:
        unit = "wicket" if margin_wickets == 1 else "wickets"
        return f"{winner_name} won by {margin_wickets} {unit}"
    if margin_runs is not None:
        unit = "run" if margin_runs == 1 else "runs"
        return f"{winner_name} won by {margin_runs} {unit}"
    return f"{winner_name} won"


def run_rate(runs: int, legal_balls: int, balls_per_over: int) -> float | None:
    if legal_balls <= 0:
        return None
    return runs / legal_balls * balls_per_over


def required_runs(target_runs: int | None, current_runs: int) -> int | None:
    if target_runs is None:
        return None
    return max(target_runs - current_runs, 0)


def balls_remaining(maximum_legal_balls: int, legal_balls: int) -> int:
    return max(maximum_legal_balls - legal_balls, 0)


def required_run_rate(
    *,
    target_runs: int | None,
    current_runs: int,
    maximum_legal_balls: int,
    legal_balls: int,
    balls_per_over: int,
) -> float | None:
    needed = required_runs(target_runs, current_runs)
    remaining = balls_remaining(maximum_legal_balls, legal_balls)
    if needed is None:
        return None
    if needed == 0:
        return 0.0
    if remaining <= 0:
        return None
    return needed / remaining * balls_per_over


def economy(runs_conceded: int, legal_balls: int, balls_per_over: int) -> float | None:
    return run_rate(runs_conceded, legal_balls, balls_per_over)


def strike_rate(runs: int, balls_faced: int) -> float | None:
    if balls_faced <= 0:
        return None
    return runs / balls_faced * 100


def round_rate(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def scorecard_rate(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(value, 2)


def over_label(
    *,
    runs_off_bat: int,
    wides: int,
    no_balls: int,
    byes: int,
    leg_byes: int,
    penalty_runs: int,
    wicket: bool,
    team_runs: int,
) -> str:
    if wicket and team_runs == 0:
        return "W"
    if wicket:
        return f"{team_runs}W"
    if wides:
        return "WD" if wides == 1 else f"{wides}WD"
    if no_balls:
        extras = runs_off_bat + byes + leg_byes
        return "NB" if extras == 0 else f"{extras}NB"
    if byes:
        return f"{byes}B"
    if leg_byes:
        return f"{leg_byes}LB"
    if penalty_runs and runs_off_bat == 0:
        return f"{penalty_runs}P"
    if runs_off_bat == 0:
        return "."
    return str(runs_off_bat)
