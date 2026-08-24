from app.cricket.formatters import format_result
from app.cricket.types import ResultType


def test_format_result_win_by_runs_and_wickets() -> None:
    assert (
        format_result(
            result_type=ResultType.WON,
            winner_name="Weekend Warriors",
            margin_runs=12,
            margin_wickets=None,
        )
        == "Weekend Warriors won by 12 runs"
    )
    assert (
        format_result(
            result_type=ResultType.WON,
            winner_name="Office XI",
            margin_runs=None,
            margin_wickets=1,
        )
        == "Office XI won by 1 wicket"
    )


def test_format_result_tie_has_no_winner() -> None:
    assert (
        format_result(
            result_type=ResultType.TIED,
            winner_name=None,
            margin_runs=None,
            margin_wickets=None,
        )
        == "Match tied"
    )
