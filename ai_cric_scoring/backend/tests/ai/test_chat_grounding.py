from uuid import uuid4

from tests.ai.fakes import grounded_chat
from tests.ai.test_fact_package import _scorecard

from app.ai.context.fact_package import assemble_fact_package
from app.ai.services.chat_grounding import ChatGroundingValidator
from app.core.exceptions import AIGroundingFailedError


def test_chat_grounding_rejects_unknown_fact_and_player() -> None:
    package = assemble_fact_package(_scorecard())
    validator = ChatGroundingValidator()
    validator.validate(grounded_chat(package), package)
    bad_fact = grounded_chat(package).model_copy(update={"fact_ids": ["fake_99"]})
    try:
        validator.validate(bad_fact, package)
        raise AssertionError("expected grounding failure")
    except AIGroundingFailedError:
        pass
    bad_player = grounded_chat(package).model_copy(update={"match_player_ids": [uuid4()]})
    try:
        validator.validate(bad_player, package)
        raise AssertionError("expected grounding failure")
    except AIGroundingFailedError:
        pass
    bad_team = grounded_chat(package).model_copy(update={"match_team_ids": [uuid4()]})
    try:
        validator.validate(bad_team, package)
        raise AssertionError("expected grounding failure")
    except AIGroundingFailedError:
        pass
