from uuid import uuid4

import pytest
from tests.ai.fakes import analysis_with_fact, analysis_with_player, analysis_with_team, grounded_analysis
from tests.ai.test_fact_package import _scorecard

from app.ai.context.fact_package import assemble_fact_package
from app.ai.services.grounding import GroundingValidator
from app.core.exceptions import AIGroundingFailedError


def test_grounding_accepts_valid_analysis() -> None:
    package = assemble_fact_package(_scorecard())
    GroundingValidator().validate(grounded_analysis(package), package)


def test_grounding_rejects_unknown_fact_id() -> None:
    package = assemble_fact_package(_scorecard())
    with pytest.raises(AIGroundingFailedError):
        GroundingValidator().validate(analysis_with_fact(package, "fake_99"), package)


def test_grounding_rejects_unknown_player() -> None:
    package = assemble_fact_package(_scorecard())
    with pytest.raises(AIGroundingFailedError):
        GroundingValidator().validate(analysis_with_player(package, uuid4()), package)


def test_grounding_rejects_unknown_team() -> None:
    package = assemble_fact_package(_scorecard())
    with pytest.raises(AIGroundingFailedError):
        GroundingValidator().validate(analysis_with_team(package, uuid4()), package)


def test_grounding_rejects_ungrounded_number() -> None:
    package = assemble_fact_package(_scorecard())
    analysis = grounded_analysis(package)
    tainted = analysis.winning_factors[0].model_copy(update={"insight": "Rahul scored 999 from 41 balls."})
    with pytest.raises(AIGroundingFailedError):
        GroundingValidator().validate(analysis.model_copy(update={"winning_factors": [tainted]}), package)
