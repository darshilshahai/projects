from tests.ai.eval_fixtures import EVAL_FIXTURES
from tests.ai.fakes import grounded_analysis

from app.ai.services.grounding import GroundingValidator


def test_evaluation_fixtures_have_required_facts_and_ground() -> None:
    validator = GroundingValidator()
    for name, factory in EVAL_FIXTURES.items():
        package = factory()
        types = {item.type for item in package.facts}
        assert {"match", "result", "batting", "bowling", "innings"} <= types, name
        assert package.potm_candidates, name
        if name == "low_scoring_tie":
            assert package.result.result_type == "TIED"
        else:
            assert package.result.winner_match_team_id is not None
        validator.validate(grounded_analysis(package), package)
