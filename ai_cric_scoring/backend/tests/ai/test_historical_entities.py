from uuid import uuid4

from app.ai.routing.historical_entities import resolve_historical_entities
from app.ai.routing.historical_router import HistoricalQuestionRouter
from app.models.enums import BattingStyle, BowlingStyle, PlayerRole
from app.models.player import Player
from app.models.team import Team

ROUTER = HistoricalQuestionRouter()


def _player(name: str) -> Player:
    return Player(
        id=uuid4(),
        owner_user_id=uuid4(),
        name=name,
        player_role=PlayerRole.BATTER,
        batting_style=BattingStyle.UNKNOWN,
        bowling_style=BowlingStyle.UNKNOWN,
        is_active=True,
    )


def test_ambiguous_first_name_clarifies() -> None:
    intent = ROUTER.classify("How has Rahul performed?")
    players = [_player("Rahul Shah"), _player("Rahul Patel")]
    resolution = resolve_historical_entities("How has Rahul performed?", intent, players, [])
    assert resolution.needs_player_clarification
    assert {item.name for item in resolution.ambiguous_players} == {"Rahul Shah", "Rahul Patel"}


def test_unique_player_resolves() -> None:
    intent = ROUTER.classify("What is Rahul's average?")
    player = _player("Rahul Shah")
    resolution = resolve_historical_entities("What is Rahul's average?", intent, [player], [])
    assert not resolution.needs_player_clarification
    assert resolution.players[0].name == "Rahul Shah"


def test_full_name_beats_shared_prefix() -> None:
    intent = ROUTER.classify("What is QueryA 0's average?")
    players = [_player("QueryA 0"), _player("QueryA 1"), _player("QueryA Opp 0"), _player("QueryA Opp 1")]
    resolution = resolve_historical_entities("What is QueryA 0's average?", intent, players, [])
    assert not resolution.needs_player_clarification
    assert [item.name for item in resolution.players] == ["QueryA 0"]


def test_exact_team_name_beats_prefixed_opponent() -> None:
    intent = ROUTER.classify("Why have Warriors been losing recently?")
    teams = [
        Team(id=uuid4(), owner_user_id=uuid4(), name="Warriors", short_name="WAR", is_active=True),
        Team(id=uuid4(), owner_user_id=uuid4(), name="Warriors Opp", short_name="WOP", is_active=True),
    ]
    resolution = resolve_historical_entities("Why have Warriors been losing recently?", intent, [], teams)
    assert not resolution.needs_team_clarification
    assert [item.name for item in resolution.teams] == ["Warriors"]
