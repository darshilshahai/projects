from __future__ import annotations

import re

from app.ai.schemas.historical import HistoricalAnswerType, HistoricalIntent, HistoricalQuestionType
from app.analytics.history.definitions import LAST_N_MAX, LAST_N_MIN, RECENT_APPEARANCES
from app.models.enums import MatchFormat

_LAST_N = re.compile(r"\blast\s+(\d+)\s+(?:matches?|appearances?|games?|innings)\b", re.I)
_RECENT = re.compile(r"\b(recent(?:ly)?|in form|current form)\b", re.I)
_SEASON = re.compile(r"\b(this season|the season|current season)\b", re.I)
_T20 = re.compile(r"\bt20\b", re.I)
_ODI = re.compile(r"\bodi\b", re.I)
_T10 = re.compile(r"\bt10\b", re.I)
_AVERAGE = re.compile(r"\b(batting )?average\b|\bwhat is .+ average\b", re.I)
_STRIKE = re.compile(r"\bstrike rate\b", re.I)
_HIGHEST = re.compile(r"\bhighest score\b|\bhigh score\b", re.I)
_RUNS = re.compile(r"\bhow many runs\b|\bscored the most runs\b|\bmost runs\b", re.I)
_WICKETS = re.compile(r"\bhow many wickets\b|\bmost wickets\b|\btaken the most wickets\b", re.I)
_ECONOMY = re.compile(r"\bbest economy\b|\beconomy\b", re.I)
_WIN_PCT = re.compile(r"\bwin (?:rate|percentage|pct)\b|\bhow many .+ won\b", re.I)
_COMPARE = re.compile(r"\bcompare\b|\bvs\.?\b|\bversus\b", re.I)
_MORE_EFFECTIVE = re.compile(
    r"\b(more effective|who(?:'s| is) better|form changed|improving|why .*(lost|losing|struggled))\b", re.I
)
_TREND = re.compile(r"\b(improving|gotten better|form changed|death overs|chasing)\b", re.I)
_RANKING = re.compile(r"\bwho has (?:scored|taken|the (?:most|best|highest))\b", re.I)
_HEAD = re.compile(r"\bhead[- ]to[- ]head\b|\bagainst each other\b", re.I)
_FORM_CHANGED = re.compile(r"\b(form changed|been recently|last \d+ matches)\b", re.I)
_OUT = re.compile(r"\b(ipl|world cricket|career in tests|best player in the world)\b", re.I)


class HistoricalQuestionRouter:
    def classify(self, question: str) -> HistoricalIntent:
        text = question.strip()
        last_n = _parse_last_n(text)
        fmt = _parse_format(text)
        if _SEASON.search(text):
            return HistoricalIntent(
                type=HistoricalQuestionType.UNKNOWN,
                answer_type=HistoricalAnswerType.CLARIFICATION,
                season_clarification=True,
            )
        if _OUT.search(text):
            return HistoricalIntent(
                type=HistoricalQuestionType.UNKNOWN,
                answer_type=HistoricalAnswerType.OUT_OF_SCOPE,
                out_of_scope=True,
            )
        if _HEAD.search(text) or (_COMPARE.search(text) and "xi" in text.lower() and "warrior" in text.lower()):
            return HistoricalIntent(
                type=HistoricalQuestionType.HEAD_TO_HEAD,
                last_n=last_n,
                format=fmt,
            )
        if _COMPARE.search(text) and not _MORE_EFFECTIVE.search(text):
            kind = (
                HistoricalQuestionType.TEAM_COMPARISON
                if _looks_team(text)
                else HistoricalQuestionType.PLAYER_COMPARISON
            )
            return HistoricalIntent(type=kind, last_n=last_n, format=fmt)
        if _MORE_EFFECTIVE.search(text) or (_TREND.search(text) and _FORM_CHANGED.search(text)):
            qtype = HistoricalQuestionType.HISTORICAL_TREND
            if _looks_team(text):
                qtype = HistoricalQuestionType.TEAM_FORM
            elif _COMPARE.search(text):
                qtype = HistoricalQuestionType.PLAYER_COMPARISON
            return HistoricalIntent(
                type=qtype,
                requires_llm=True,
                answer_type=HistoricalAnswerType.ANALYTICAL,
                last_n=last_n or RECENT_APPEARANCES,
                format=fmt,
            )
        if _RANKING.search(text) or (_RUNS.search(text) and "who" in text.lower()):
            metric = "wickets" if _WICKETS.search(text) else "runs"
            if _ECONOMY.search(text):
                metric = "economy"
            if "average" in text.lower():
                metric = "batting_average"
            return HistoricalIntent(
                type=HistoricalQuestionType.PLAYER_RANKING,
                ranking_metric=metric,
                last_n=last_n,
                format=fmt,
            )
        if _WIN_PCT.search(text) or ("won" in text.lower() and _looks_team(text)):
            return HistoricalIntent(type=HistoricalQuestionType.TEAM_STATS, last_n=last_n, format=fmt)
        if re.search(r"\bdeath overs?\b", text, re.I) or (
            _TREND.search(text) and ("improved" in text.lower() or "trend" in text.lower())
        ):
            qtype = HistoricalQuestionType.TEAM_FORM if _looks_team(text) else HistoricalQuestionType.HISTORICAL_TREND
            return HistoricalIntent(
                type=qtype,
                requires_llm=True,
                answer_type=HistoricalAnswerType.ANALYTICAL,
                last_n=last_n or RECENT_APPEARANCES,
                format=fmt,
                unavailable_topic="death_overs" if re.search(r"\bdeath overs?\b", text, re.I) else None,
            )
        if _RECENT.search(text) and not _MORE_EFFECTIVE.search(text):
            qtype = HistoricalQuestionType.TEAM_FORM if _looks_team(text) else HistoricalQuestionType.PLAYER_FORM
            return HistoricalIntent(type=qtype, last_n=last_n or RECENT_APPEARANCES, format=fmt)
        if _AVERAGE.search(text) or _STRIKE.search(text) or _HIGHEST.search(text) or _WICKETS.search(text):
            qtype = HistoricalQuestionType.TEAM_STATS if _looks_team(text) else HistoricalQuestionType.PLAYER_STATS
            return HistoricalIntent(type=qtype, last_n=last_n, format=fmt)
        if _looks_team(text):
            return HistoricalIntent(type=HistoricalQuestionType.TEAM_STATS, last_n=last_n, format=fmt)
        if _has_person_hint(text):
            return HistoricalIntent(type=HistoricalQuestionType.PLAYER_STATS, last_n=last_n, format=fmt)
        return HistoricalIntent(
            type=HistoricalQuestionType.UNKNOWN,
            answer_type=HistoricalAnswerType.OUT_OF_SCOPE,
            out_of_scope=True,
        )


def _parse_last_n(text: str) -> int | None:
    match = _LAST_N.search(text)
    if not match:
        return None
    value = int(match.group(1))
    return max(LAST_N_MIN, min(LAST_N_MAX, value))


def _parse_format(text: str) -> MatchFormat | None:
    if _T20.search(text):
        return MatchFormat.T20
    if _ODI.search(text):
        return MatchFormat.ODI
    if _T10.search(text):
        return MatchFormat.T10
    return None


def _looks_team(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("warriors", "office", "team", "xi", "we ", "our ", "us "))


def _has_person_hint(text: str) -> bool:
    return bool(re.search(r"\b[A-Z][a-z]+\b", text)) or "player" in text.lower()
