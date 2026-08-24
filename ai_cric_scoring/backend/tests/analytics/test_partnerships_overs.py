from uuid import uuid4

from app.analytics.extras import calculate_extras
from app.analytics.overs import build_over_summaries
from app.analytics.partnerships import build_partnerships
from app.analytics.types import DeliveryFact
from app.cricket.types import DismissalType


def _ball(
    *,
    sequence: int,
    over: int,
    striker,
    non_striker,
    bowler,
    runs: int = 0,
    wides: int = 0,
    no_balls: int = 0,
    byes: int = 0,
    legal: bool = True,
    wicket: DismissalType | None = None,
    dismissed=None,
) -> DeliveryFact:
    return DeliveryFact(
        sequence_number=sequence,
        over_number=over,
        striker_id=striker,
        non_striker_id=non_striker,
        bowler_id=bowler,
        runs_off_bat=runs,
        wides=wides,
        no_balls=no_balls,
        byes=byes,
        leg_byes=0,
        penalty_runs=0,
        is_legal=legal,
        dismissal_type=wicket,
        dismissed_player_id=dismissed,
    )


def test_opening_and_wicket_partnerships() -> None:
    a, b, c, bowl = uuid4(), uuid4(), uuid4(), uuid4()
    deliveries = [
        _ball(sequence=1, over=1, striker=a, non_striker=b, bowler=bowl, runs=4),
        _ball(sequence=2, over=1, striker=a, non_striker=b, bowler=bowl, runs=1),
        _ball(
            sequence=3,
            over=1,
            striker=b,
            non_striker=a,
            bowler=bowl,
            wicket=DismissalType.BOWLED,
            dismissed=b,
        ),
        _ball(sequence=4, over=1, striker=c, non_striker=a, bowler=bowl, runs=2),
    ]
    stands = build_partnerships(deliveries, innings_complete=False)
    assert len(stands) == 2
    assert stands[0].runs == 5
    assert stands[0].is_current is False
    assert stands[0].end_score == 5
    assert stands[1].batter_1_id == a
    assert stands[1].batter_2_id == c
    assert stands[1].runs == 2
    assert stands[1].is_current is True
    assert stands[1].start_score == 5


def test_extras_and_over_summaries() -> None:
    a, b, bowl = uuid4(), uuid4(), uuid4()
    deliveries = [
        _ball(sequence=1, over=1, striker=a, non_striker=b, bowler=bowl, wides=1, legal=False),
        _ball(sequence=2, over=1, striker=a, non_striker=b, bowler=bowl, runs=4, no_balls=1, legal=False),
        _ball(sequence=3, over=1, striker=a, non_striker=b, bowler=bowl, byes=2),
        _ball(sequence=4, over=1, striker=a, non_striker=b, bowler=bowl, runs=1),
    ]
    extras = calculate_extras(deliveries)
    assert extras.total == 4
    assert extras.wides == 1
    assert extras.no_balls == 1
    assert extras.byes == 2
    overs = build_over_summaries(deliveries, balls_per_over=6)
    assert len(overs) == 1
    assert overs[0].runs == 9
    assert overs[0].legal_balls == 2
    assert overs[0].is_complete is False
    assert overs[0].deliveries[0].label == "WD"
    assert overs[0].deliveries[1].label == "4NB"
