from app.analytics.dismissals import format_dismissal


def test_format_common_dismissals() -> None:
    assert format_dismissal(status="BATTING", dismissal_type=None) == "not out"
    assert format_dismissal(status="OUT", dismissal_type="BOWLED", bowler_name="Dev") == "b Dev"
    assert (
        format_dismissal(status="OUT", dismissal_type="CAUGHT", bowler_name="Dev", fielder_name="Jay") == "c Jay b Dev"
    )
    assert format_dismissal(status="OUT", dismissal_type="LBW", bowler_name="Arjun") == "lbw b Arjun"
    assert (
        format_dismissal(status="OUT", dismissal_type="STUMPED", bowler_name="Arjun", fielder_name="Dev")
        == "st Dev b Arjun"
    )
    assert format_dismissal(status="OUT", dismissal_type="RUN_OUT", fielder_name="Jay") == "run out (Jay)"
    assert format_dismissal(status="OUT", dismissal_type="HIT_WICKET", bowler_name="Dev") == "hit wicket b Dev"


def test_format_retired_and_fallbacks() -> None:
    assert format_dismissal(status="RETIRED_HURT", dismissal_type=None) == "retired hurt"
    assert format_dismissal(status="RETIRED_OUT", dismissal_type="RETIRED_OUT") == "retired out"
    assert format_dismissal(status="OUT", dismissal_type="CAUGHT", bowler_name="Dev") == "c unknown b Dev"
    assert format_dismissal(status="OUT", dismissal_type="RUN_OUT") == "run out"
    assert format_dismissal(status="OUT", dismissal_type="OBSTRUCTING_THE_FIELD") == "obstructing the field"
