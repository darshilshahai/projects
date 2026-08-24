from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.ai.context.fact_package import MatchFactPackage
from app.ai.schemas.historical import StructuredHistoricalInsight
from app.ai.schemas.match_analysis import AnalysisSection, PlayerOfMatchRecommendation, StructuredMatchAnalysis
from app.ai.schemas.match_chat import StructuredChatAnswer
from app.ai.schemas.provider import StructuredGeneration
from app.core.exceptions import AIInvalidResponseError


class FakeAIProvider:
    def __init__(
        self,
        response: StructuredMatchAnalysis | None = None,
        error: Exception | None = None,
        errors: list[Exception] | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.errors = list(errors or [])
        self.calls = 0
        self.system_prompts: list[str] = []
        self.user_prompts: list[str] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> StructuredGeneration[Any]:
        self.calls += 1
        self.system_prompts.append(system_prompt)
        self.user_prompts.append(user_prompt)
        if self.errors:
            raise self.errors.pop(0)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AIInvalidResponseError("No fake analysis configured.")
        data = self.response
        if isinstance(data, StructuredHistoricalInsight):
            start = user_prompt.find("BEGIN HISTORICAL DATA")
            end = user_prompt.find("END HISTORICAL DATA")
            if start != -1 and end != -1:
                raw = user_prompt[start + len("BEGIN HISTORICAL DATA") : end].strip()
                try:
                    payload = json.loads(raw)
                    fact_ids = [item["id"] for item in payload.get("facts", [])][:2]
                    if fact_ids:
                        data = data.model_copy(update={"fact_ids": fact_ids})
                except json.JSONDecodeError:
                    pass
        if not isinstance(data, response_model):
            raise AIInvalidResponseError("Fake provider response did not match the requested schema.")
        return StructuredGeneration(
            data=self.response,
            provider="fake",
            model="fake-model",
            input_tokens=12,
            output_tokens=34,
            latency_ms=8,
        )


def grounded_analysis(package: MatchFactPackage) -> StructuredMatchAnalysis:
    usable = [
        item.id
        for item in package.facts
        if item.type in {"result", "innings", "batting", "bowling", "partnership", "phase", "key_event"}
    ]
    fact_id = usable[0] if usable else "result"
    potm = package.potm_candidates[0]
    section = AnalysisSection(
        title="Middle-order stability",
        insight="The innings stabilized after early pressure and the bowling side could not break the stand.",
        fact_ids=[fact_id],
        importance="HIGH",
    )
    return StructuredMatchAnalysis(
        headline="Grounded middle-order stand decides the match",
        summary=(
            "The batting side built a platform through a key partnership. "
            "The bowling side created pressure but could not force a collapse. "
            "The result followed the recorded scores rather than unrecorded fielding."
        ),
        winning_factors=[section],
        losing_factors=[
            AnalysisSection(
                title="Late wickets",
                insight="Wickets in the closing phase reduced momentum.",
                fact_ids=[fact_id],
                importance="MEDIUM",
            )
        ],
        batting_analysis=[section.model_copy(update={"match_player_id": potm.match_player_id})],
        bowling_analysis=[section],
        partnership_analysis=[section],
        phase_analysis=[section],
        turning_points=[section.model_copy(update={"event_type": "PARTNERSHIP"})],
        key_moments=[section],
        tactical_observations=[section],
        recommendations=[section],
        player_of_match=PlayerOfMatchRecommendation(
            match_player_id=potm.match_player_id,
            reason="Led the supplied candidate contributions with bat and or ball.",
            confidence="HIGH",
            fact_ids=potm.fact_ids[:1] or [fact_id],
        ),
        winning_match_team_id=package.result.winner_match_team_id,
    )


def analysis_with_fact(package: MatchFactPackage, fact_id: str) -> StructuredMatchAnalysis:
    body = grounded_analysis(package)
    tainted = body.winning_factors[0].model_copy(update={"fact_ids": [fact_id]})
    return body.model_copy(update={"winning_factors": [tainted]})


def analysis_with_player(package: MatchFactPackage, player_id: UUID) -> StructuredMatchAnalysis:
    body = grounded_analysis(package)
    return body.model_copy(
        update={
            "player_of_match": body.player_of_match.model_copy(update={"match_player_id": player_id}),
        }
    )


def analysis_with_team(package: MatchFactPackage, team_id: UUID) -> StructuredMatchAnalysis:
    body = grounded_analysis(package)
    return body.model_copy(update={"winning_match_team_id": team_id})


def grounded_chat(package: MatchFactPackage) -> StructuredChatAnswer:
    usable = [item.id for item in package.facts if item.type in {"result", "innings", "batting", "partnership"}]
    return StructuredChatAnswer(
        content="The bowling side could not break the stand after early wickets, and that contributed to the result.",
        fact_ids=[usable[0] if usable else "result"],
        match_player_ids=[],
        match_team_ids=[package.result.winner_match_team_id] if package.result.winner_match_team_id else [],
        confidence="MEDIUM",
    )
