from __future__ import annotations

from app.ai.routing.question_router import MatchQuestionRouter
from app.ai.schemas.match_chat import AnswerType, QuestionType

ROUTER = MatchQuestionRouter()

EVAL_QUESTIONS = [
    {"q": "Who won the match?", "type": QuestionType.MATCH_SUMMARY, "llm": False},
    {"q": "What was the final score?", "type": QuestionType.MATCH_SUMMARY, "llm": False},
    {"q": "What was the target?", "type": QuestionType.MATCH_SUMMARY, "llm": False},
    {"q": "How many runs did Rahul score?", "type": QuestionType.DIRECT_STAT, "llm": False},
    {"q": "What was Rahul's score?", "type": QuestionType.DIRECT_STAT, "llm": False},
    {"q": "How many did Rahul score?", "type": QuestionType.DIRECT_STAT, "llm": False},
    {"q": "Who was the top scorer?", "type": QuestionType.BATTING, "llm": False},
    {"q": "Who had the best strike rate?", "type": QuestionType.BATTING, "llm": False},
    {"q": "Who took the most wickets?", "type": QuestionType.BOWLING, "llm": False},
    {"q": "How many extras were there?", "type": QuestionType.EXTRAS, "llm": False},
    {"q": "How many extras did Team A concede?", "type": QuestionType.EXTRAS, "llm": False},
    {"q": "Did extras make a big difference?", "type": QuestionType.EXTRAS, "llm": True},
    {"q": "What was the biggest partnership?", "type": QuestionType.PARTNERSHIP, "llm": False},
    {"q": "Which partnership changed the match?", "type": QuestionType.TURNING_POINT, "llm": True},
    {"q": "What happened in the last 5 overs?", "type": QuestionType.OVER_RANGE, "llm": False},
    {"q": "What happened between overs 15 and 20?", "type": QuestionType.OVER_RANGE, "llm": False},
    {"q": "Why did Team B lose?", "type": QuestionType.WHY_RESULT, "llm": True},
    {"q": "Where did the chase go wrong?", "type": QuestionType.WHY_RESULT, "llm": True},
    {"q": "Compare Rahul and Dev.", "type": QuestionType.COMPARISON, "llm": True},
    {"q": "Who scored more, Rahul or Dev?", "type": QuestionType.COMPARISON, "llm": False},
    {"q": "Who dismissed Rahul?", "type": QuestionType.DIRECT_STAT, "llm": False},
    {"q": "How did Rahul bat?", "type": QuestionType.PLAYER_PERFORMANCE, "llm": True},
    {"q": "Who bowled the best spell?", "type": QuestionType.BOWLING, "llm": True},
    {"q": "Who fielded best?", "type": QuestionType.FIELDING, "llm": False},
    {"q": "Who took the most catches?", "type": QuestionType.FIELDING, "llm": False},
    {"q": "What was the weather?", "type": QuestionType.UNKNOWN, "llm": False},
    {"q": "What was the pitch like?", "type": QuestionType.UNKNOWN, "llm": False},
    {"q": "Who won the IPL last year?", "type": QuestionType.UNKNOWN, "llm": False},
    {"q": "Who is the best player in world cricket?", "type": QuestionType.UNKNOWN, "llm": False},
    {"q": "How did Rahul play in the previous match?", "type": QuestionType.UNKNOWN, "llm": False},
]


def test_eval_questions_classify_without_llm_when_direct() -> None:
    for item in EVAL_QUESTIONS:
        intent = ROUTER.classify(item["q"])
        assert intent.type is item["type"], item["q"]
        assert intent.requires_llm is item["llm"], item["q"]
        if item["llm"]:
            assert intent.answer_type is AnswerType.ANALYTICAL
        if "IPL" in item["q"] or "world cricket" in item["q"] or "previous match" in item["q"]:
            assert intent.out_of_scope is True
        if "weather" in item["q"] or "pitch" in item["q"]:
            assert intent.unavailable_topic == "conditions"
