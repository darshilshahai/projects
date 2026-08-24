from uuid import uuid4

from app.ai.schemas.historical import StructuredHistoricalInsight
from app.ai.services.historical_grounding import HistoricalGroundingValidator
from app.core.exceptions import AIGroundingFailedError


def test_historical_grounding_rejects_out_of_scope_fact() -> None:
    package = {
        "fact_index": [{"id": "player_abc_last5", "type": "trend", "label": "avg"}],
        "player_ids": [],
        "team_ids": [],
        "allowed_numbers": {"5", "42"},
        "facts": [],
    }
    validator = HistoricalGroundingValidator()
    ok = StructuredHistoricalInsight(summary="Recent form improved.", fact_ids=["player_abc_last5"])
    validator.validate(ok, package)
    bad = StructuredHistoricalInsight(summary="All-time dominance.", fact_ids=["player_abc_alltime"])
    try:
        validator.validate(bad, package)
        raise AssertionError("expected grounding failure")
    except AIGroundingFailedError:
        pass
    unknown_player = StructuredHistoricalInsight(
        summary="Recent form improved.",
        fact_ids=["player_abc_last5"],
        player_ids=[uuid4()],
    )
    try:
        validator.validate(unknown_player, package)
        raise AssertionError("expected grounding failure")
    except AIGroundingFailedError:
        pass
