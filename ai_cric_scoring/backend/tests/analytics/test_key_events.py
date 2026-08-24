from uuid import uuid4

from app.analytics.key_events import detect_key_events
from app.schemas.scorecard import FallOfWicketRow, OverSummaryRow, PartnershipRow


def test_wicket_cluster_and_collapse_thresholds() -> None:
    player = uuid4()
    fow = [
        FallOfWicketRow(wicket_number=1, score=10, player_id=player, player_name="A", legal_balls=8, overs="1.2"),
        FallOfWicketRow(wicket_number=2, score=14, player_id=player, player_name="B", legal_balls=12, overs="2.0"),
        FallOfWicketRow(wicket_number=3, score=18, player_id=player, player_name="C", legal_balls=16, overs="2.4"),
    ]
    events = detect_key_events(
        innings_number=1,
        overs=[],
        fall_of_wickets=fow,
        partnerships=[],
        balls_per_over=6,
        target=None,
    )
    types = {item.event_type for item in events}
    assert "WICKET_CLUSTER" in types
    assert "COLLAPSE" in types


def test_top_overs_and_partnerships() -> None:
    overs = [
        OverSummaryRow(over_number=1, runs=16, wickets=0, legal_balls=6, is_complete=True),
        OverSummaryRow(over_number=2, runs=2, wickets=2, legal_balls=6, is_complete=True),
        OverSummaryRow(over_number=3, runs=9, wickets=1, legal_balls=6, is_complete=True),
    ]
    batter_a = uuid4()
    batter_b = uuid4()
    partnerships = [
        PartnershipRow(
            batter_1_id=batter_a,
            batter_1_name="Rahul",
            batter_2_id=batter_b,
            batter_2_name="Dev",
            runs=68,
            legal_balls=43,
            start_score=20,
            end_score=88,
            is_current=False,
            batter_1_runs=40,
            batter_2_runs=28,
        )
    ]
    events = detect_key_events(
        innings_number=1,
        overs=overs,
        fall_of_wickets=[],
        partnerships=partnerships,
        balls_per_over=6,
        target=None,
    )
    high = [item for item in events if item.event_type == "HIGH_SCORING_OVER"]
    wickets = [item for item in events if item.event_type == "WICKET_OVER"]
    stands = [item for item in events if item.event_type == "LARGE_PARTNERSHIP"]
    assert high[0].values["runs"] == 16
    assert wickets[0].values["wickets"] == 2
    assert stands[0].values["runs"] == 68
