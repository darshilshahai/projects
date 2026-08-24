from app.analytics.phases import define_analytical_phases, summarize_phases
from app.models.enums import MatchFormat
from app.schemas.scorecard import OverDeliveryRow, OverSummaryRow


def test_standard_format_phase_ranges() -> None:
    t20 = define_analytical_phases(MatchFormat.T20, 20)
    assert [(item.key, item.start_over, item.end_over) for item in t20] == [
        ("opening", 1, 6),
        ("middle", 7, 15),
        ("closing", 16, 20),
    ]
    assert "analytical" in t20[0].label.lower()
    odi = define_analytical_phases(MatchFormat.ODI, 50)
    assert [(item.start_over, item.end_over) for item in odi] == [(1, 10), (11, 40), (41, 50)]
    t10 = define_analytical_phases(MatchFormat.T10, 10)
    assert [(item.start_over, item.end_over) for item in t10] == [(1, 3), (4, 7), (8, 10)]


def test_custom_phases_are_proportional_and_not_powerplay() -> None:
    custom = define_analytical_phases(MatchFormat.CUSTOM, 10)
    assert [(item.key, item.start_over, item.end_over) for item in custom] == [
        ("opening", 1, 3),
        ("middle", 4, 7),
        ("closing", 8, 10),
    ]
    assert all("Powerplay" not in item.label for item in custom)
    short = define_analytical_phases(MatchFormat.CUSTOM, 1)
    assert len(short) == 1
    assert short[0].key == "opening"
    assert short[0].end_over == 1


def test_phase_stats_use_over_summaries() -> None:
    overs = [
        OverSummaryRow(
            over_number=1,
            runs=10,
            wickets=1,
            legal_balls=6,
            is_complete=True,
            deliveries=[
                OverDeliveryRow(label="4", runs=4, wicket=False, legal=True),
                OverDeliveryRow(label=".", runs=0, wicket=False, legal=True),
            ],
        ),
        OverSummaryRow(over_number=2, runs=8, wickets=0, legal_balls=6, is_complete=True),
    ]
    phases = summarize_phases(
        overs,
        match_format=MatchFormat.CUSTOM,
        overs_per_innings=2,
        balls_per_over=6,
    )
    assert [item.key for item in phases] == ["opening", "closing"]
    assert phases[0].runs == 10
    assert phases[0].wickets == 1
    assert phases[0].boundaries == 1
    assert phases[0].dots == 1
    assert phases[1].runs == 8
