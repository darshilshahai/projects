from uuid import uuid4

from tests.ai.test_fact_package import _scorecard

from app.ai.context.fact_package import assemble_fact_package
from app.ai.routing.entity_resolver import resolve_entities
from app.ai.routing.question_router import MatchQuestionRouter
from app.schemas.scorecard import BattingScorecardRow

ROUTER = MatchQuestionRouter()


def test_ambiguous_first_name_requires_clarification() -> None:
    scorecard = _scorecard(batter="Rahul Shah")
    second = BattingScorecardRow(
        match_player_id=uuid4(),
        name="Rahul Patel",
        batting_position=2,
        runs=20,
        balls=18,
        fours=2,
        sixes=0,
        strike_rate=111.11,
        status="out",
        dismissal_text="b Dev",
    )
    scorecard.innings[0].batting.append(second)
    package = assemble_fact_package(scorecard)
    intent = ROUTER.classify("How many did Rahul score?")
    resolution = resolve_entities("How many did Rahul score?", intent, package)
    assert resolution.needs_player_clarification
    assert {item.name for item in resolution.ambiguous_players} == {"Rahul Shah", "Rahul Patel"}


def test_unique_first_name_resolves() -> None:
    package = assemble_fact_package(_scorecard())
    intent = ROUTER.classify("How many runs did Rahul score?")
    resolution = resolve_entities("How many runs did Rahul score?", intent, package)
    assert not resolution.needs_player_clarification
    assert resolution.players[0].name == "Rahul Shah"


def test_follow_up_pronoun_uses_last_player() -> None:
    package = assemble_fact_package(_scorecard())
    batter = next(item for item in package.facts if item.type == "batting")
    intent = ROUTER.classify("Who dismissed him?")
    resolution = resolve_entities(
        "Who dismissed him?",
        intent,
        package,
        last_player_id=batter.match_player_id,
    )
    assert resolution.players[0].match_player_id == batter.match_player_id


def test_follow_up_their_uses_last_team() -> None:
    package = assemble_fact_package(_scorecard())
    team_id = package.match.team_b_id
    intent = ROUTER.classify("What was their biggest partnership?")
    resolution = resolve_entities(
        "What was their biggest partnership?",
        intent,
        package,
        last_team_id=team_id,
    )
    assert resolution.teams[0].match_team_id == team_id
    assert resolution.teams[0].name == package.match.team_b_name
