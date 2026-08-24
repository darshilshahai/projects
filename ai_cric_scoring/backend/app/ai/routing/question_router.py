from __future__ import annotations

import re

from app.ai.schemas.match_chat import AnswerType, ContextMode, QuestionIntent, QuestionType

_LAST_OVERS = re.compile(r"\blast\s+(\d+)\s+overs?\b", re.I)
_OVER_RANGE = re.compile(
    r"\bovers?\s+(\d+)\s*(?:to|-|and)\s*(\d+)\b|\bbetween\s+overs?\s+(\d+)\s+and\s+(\d+)\b",
    re.I,
)
_FIRST_INNINGS = re.compile(r"\b(first innings|innings 1|opening innings)\b", re.I)
_SECOND_INNINGS = re.compile(r"\b(second innings|innings 2|the chase|chasing|chase)\b", re.I)

_OUT_OF_SCOPE = re.compile(
    r"\b(previous match|last match|career|usually|form|ipl|world cricket|"
    r"best (?:player|cricketer) in the world|system prompt|ignore (?:previous|all) instructions)\b",
    re.I,
)
_UNAVAILABLE = re.compile(r"\b(weather|pitch|outfield|crowd|dropped catches?|misfield|runs saved|dew)\b", re.I)
_GREETING = re.compile(r"^(hi|hello|hey|thanks|thank you|yo)\b", re.I)

_WHO_WON = re.compile(
    r"\b(who won|winner|by how much|margin|final score|what was the (?:result|target)|who won the match)\b",
    re.I,
)
_TARGET = re.compile(r"\b(target|how many did they need|what was the target)\b", re.I)
_TOP_SCORER = re.compile(r"\b(top scorer|most runs|highest score|who scored the most)\b", re.I)
_MOST_WICKETS = re.compile(r"\b(most wickets|leading wicket|who took the most wickets)\b", re.I)
_BEST_SR = re.compile(r"\b(best strike rate|highest strike rate|highest sr)\b", re.I)
_EXTRAS_COUNT = re.compile(r"\b(how many extras|extras were there|total extras)\b", re.I)
_EXTRAS_IMPACT = re.compile(r"\b(extras (?:cost|make|matter)|did extras)\b", re.I)
_LARGEST_PSHIP = re.compile(
    r"\b(largest|biggest|highest|longest)\b.*\bpartnership\b|\bpartnership\b.*\b(largest|biggest)\b",
    re.I,
)
_COMPARE = re.compile(r"\b(compare|who scored more|who made more)\b", re.I)
_WHO_MORE = re.compile(r"\bwho (?:scored|made|took) more\b", re.I)
_WHY_RESULT = re.compile(
    r"\bwhy (?:did|have) .*(?:lose|lost|win|won)\b|\bwhere did (?:the )?(?:chase|match) go wrong\b|"
    r"\bwhy (?:they|we) (?:lose|lost|win|won)\b",
    re.I,
)
_TURNING = re.compile(r"\b(turning point|where did the match turn|which partnership changed|changed the match)\b", re.I)
_PLAYER_RUNS = re.compile(
    r"\bhow many(?: runs)? did\b|\bhow many did\b|\b(?:runs|score) did\b|\bwhat was .+\bscores?\b|\b.+'s score\b",
    re.I,
)
_HOW_BAT = re.compile(r"\bhow did\b.*\b(bat|batting|play)\b", re.I)
_HOW_BOWL = re.compile(r"\bhow did\b.*\bbowl", re.I)
_DISMISSED = re.compile(r"\b(who dismissed|how did .* get out|how (?:he|she|they) get out|how was .* out)\b", re.I)
_BOWLED_BEST = re.compile(r"\b(who bowled (?:best|well)|best spell|best bowling)\b", re.I)
_FIELD_BEST = re.compile(r"\b(who fielded best|best fielder|fielding best)\b", re.I)
_CATCHES = re.compile(r"\b(most catches|who took .*catch)\b", re.I)
_PARTNERSHIP = re.compile(r"\bpartnership\b", re.I)
_BOWLING = re.compile(r"\b(bowl|wicket|economy|spell)\b", re.I)
_BATTING = re.compile(r"\b(bat|batter|batting|strike rate)\b", re.I)
_EXTRAS = re.compile(r"\bextras?\b|\bwides?\b|\bno-?balls?\b", re.I)
_SUMMARY = re.compile(r"\b(summar(y|ise|ize)|what happened|tell me about this match)\b", re.I)


class MatchQuestionRouter:
    def classify(self, question: str) -> QuestionIntent:
        text = question.strip()
        innings_hint = _innings_hint(text)
        last_n, start, end = _overs(text)
        wants_chase = bool(_SECOND_INNINGS.search(text) and "first innings" not in text.lower())

        if _GREETING.match(text) and len(text.split()) <= 4:
            return QuestionIntent(
                type=QuestionType.UNKNOWN,
                answer_type=AnswerType.OUT_OF_SCOPE,
                out_of_scope=True,
                context_mode=ContextMode.NONE,
            )
        if _OUT_OF_SCOPE.search(text):
            return QuestionIntent(
                type=QuestionType.UNKNOWN,
                answer_type=AnswerType.OUT_OF_SCOPE,
                out_of_scope=True,
                context_mode=ContextMode.NONE,
            )
        if _UNAVAILABLE.search(text) or _FIELD_BEST.search(text):
            topic = "fielding detail" if _FIELD_BEST.search(text) else "conditions"
            if _UNAVAILABLE.search(text) and re.search(r"weather|pitch|dew|crowd|outfield", text, re.I):
                topic = "conditions"
            elif re.search(r"dropped|misfield|runs saved", text, re.I):
                topic = "unrecorded fielding"
            return QuestionIntent(
                type=QuestionType.FIELDING if topic != "conditions" else QuestionType.UNKNOWN,
                answer_type=AnswerType.DIRECT_STAT,
                unavailable_topic=topic,
                context_mode=ContextMode.NONE,
            )

        if last_n is not None or start is not None:
            return QuestionIntent(
                type=QuestionType.OVER_RANGE,
                last_n_overs=last_n,
                over_start=start,
                over_end=end,
                innings_hint=innings_hint,
                wants_chase=wants_chase,
                context_mode=ContextMode.OVER_RANGE,
            )
        if _WHY_RESULT.search(text):
            return QuestionIntent(
                type=QuestionType.WHY_RESULT,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                innings_hint=innings_hint,
                wants_chase=wants_chase,
                context_mode=ContextMode.FULL_ANALYTICAL,
            )
        if _TURNING.search(text):
            return QuestionIntent(
                type=QuestionType.TURNING_POINT,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.FULL_ANALYTICAL,
            )
        if _COMPARE.search(text):
            return QuestionIntent(
                type=QuestionType.COMPARISON,
                requires_llm=not bool(_WHO_MORE.search(text)),
                answer_type=AnswerType.DIRECT_STAT if _WHO_MORE.search(text) else AnswerType.ANALYTICAL,
                context_mode=ContextMode.COMPARISON,
            )
        if _EXTRAS_IMPACT.search(text):
            return QuestionIntent(
                type=QuestionType.EXTRAS,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.EXTRAS,
            )
        if _EXTRAS_COUNT.search(text) or (_EXTRAS.search(text) and _PLAYER_RUNS.search(text)):
            return QuestionIntent(
                type=QuestionType.EXTRAS,
                context_mode=ContextMode.EXTRAS,
            )
        if _CATCHES.search(text):
            return QuestionIntent(
                type=QuestionType.FIELDING,
                context_mode=ContextMode.FIELDING,
            )
        if _BOWLED_BEST.search(text):
            return QuestionIntent(
                type=QuestionType.BOWLING,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.PLAYER_BOWLING,
            )
        if _MOST_WICKETS.search(text):
            return QuestionIntent(type=QuestionType.BOWLING, context_mode=ContextMode.PLAYER_BOWLING)
        if _TOP_SCORER.search(text) or _BEST_SR.search(text):
            return QuestionIntent(type=QuestionType.BATTING, context_mode=ContextMode.PLAYER_BATTING)
        if _LARGEST_PSHIP.search(text):
            return QuestionIntent(type=QuestionType.PARTNERSHIP, context_mode=ContextMode.PARTNERSHIPS)
        if _PARTNERSHIP.search(text):
            return QuestionIntent(
                type=QuestionType.PARTNERSHIP,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.PARTNERSHIPS,
            )
        if _WHO_WON.search(text) or _TARGET.search(text):
            return QuestionIntent(type=QuestionType.MATCH_SUMMARY, context_mode=ContextMode.RESULT_ONLY)
        if _DISMISSED.search(text) or _PLAYER_RUNS.search(text):
            return QuestionIntent(
                type=QuestionType.DIRECT_STAT,
                context_mode=ContextMode.PLAYER_FULL,
            )
        if _HOW_BAT.search(text):
            return QuestionIntent(
                type=QuestionType.PLAYER_PERFORMANCE,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.PLAYER_BATTING,
            )
        if _HOW_BOWL.search(text):
            return QuestionIntent(
                type=QuestionType.PLAYER_PERFORMANCE,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.PLAYER_BOWLING,
            )
        if _SUMMARY.search(text):
            return QuestionIntent(
                type=QuestionType.MATCH_SUMMARY,
                requires_llm=True,
                answer_type=AnswerType.ANALYTICAL,
                context_mode=ContextMode.FULL_ANALYTICAL,
            )
        if _EXTRAS.search(text):
            return QuestionIntent(type=QuestionType.EXTRAS, context_mode=ContextMode.EXTRAS)
        if _BOWLING.search(text):
            return QuestionIntent(type=QuestionType.BOWLING, context_mode=ContextMode.PLAYER_BOWLING)
        if _BATTING.search(text):
            return QuestionIntent(type=QuestionType.BATTING, context_mode=ContextMode.PLAYER_BATTING)
        return QuestionIntent(
            type=QuestionType.UNKNOWN,
            answer_type=AnswerType.OUT_OF_SCOPE,
            out_of_scope=True,
            context_mode=ContextMode.NONE,
        )


def _innings_hint(text: str) -> int | None:
    if _FIRST_INNINGS.search(text):
        return 1
    if _SECOND_INNINGS.search(text):
        return 2
    return None


def _overs(text: str) -> tuple[int | None, int | None, int | None]:
    last = _LAST_OVERS.search(text)
    if last:
        return int(last.group(1)), None, None
    ranged = _OVER_RANGE.search(text)
    if ranged:
        start = int(ranged.group(1) or ranged.group(3))
        end = int(ranged.group(2) or ranged.group(4))
        if start > end:
            start, end = end, start
        return None, start, end
    return None, None, None
