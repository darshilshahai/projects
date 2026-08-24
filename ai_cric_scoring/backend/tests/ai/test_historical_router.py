from app.ai.routing.historical_router import HistoricalQuestionRouter
from app.ai.schemas.historical import HistoricalAnswerType, HistoricalQuestionType

ROUTER = HistoricalQuestionRouter()


def test_direct_average_does_not_need_llm() -> None:
    intent = ROUTER.classify("What is Rahul's average?")
    assert intent.type is HistoricalQuestionType.PLAYER_STATS
    assert intent.requires_llm is False


def test_recent_is_last_five_form() -> None:
    intent = ROUTER.classify("How has Rahul performed recently?")
    assert intent.type is HistoricalQuestionType.PLAYER_FORM
    assert intent.last_n == 5
    assert intent.requires_llm is False


def test_compare_is_direct() -> None:
    intent = ROUTER.classify("Compare Rahul and Dev.")
    assert intent.type is HistoricalQuestionType.PLAYER_COMPARISON
    assert intent.requires_llm is False


def test_why_losing_is_analytical() -> None:
    intent = ROUTER.classify("Why have Warriors been losing recently?")
    assert intent.requires_llm is True
    assert intent.answer_type is HistoricalAnswerType.ANALYTICAL


def test_season_asks_clarification() -> None:
    intent = ROUTER.classify("How many wickets has Dev taken this season?")
    assert intent.season_clarification is True


def test_ranking_most_runs() -> None:
    intent = ROUTER.classify("Who has scored the most runs?")
    assert intent.type is HistoricalQuestionType.PLAYER_RANKING
    assert intent.ranking_metric == "runs"
    assert intent.requires_llm is False


def test_death_overs_are_analytical() -> None:
    intent = ROUTER.classify("Has our death over bowling improved?")
    assert intent.requires_llm is True
    assert intent.answer_type is HistoricalAnswerType.ANALYTICAL
