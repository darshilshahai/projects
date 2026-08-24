from __future__ import annotations

import uuid
from typing import Any

from app.ai.prompts.historical_prompt import HistoricalPromptBuilder
from app.ai.routing.historical_entities import HistoricalResolution, NamedEntity, resolve_historical_entities
from app.ai.routing.historical_router import HistoricalQuestionRouter
from app.ai.schemas.historical import (
    HistoricalAnswerType,
    HistoricalIntent,
    HistoricalQuestionType,
    StructuredHistoricalInsight,
)
from app.ai.services.ai_service import AIService
from app.ai.services.historical_grounding import HistoricalGroundingValidator
from app.analytics.history.definitions import RECENT_APPEARANCES
from app.analytics.history.filters import HistoricalScope
from app.analytics.history.phases import aggregate_closing_phase
from app.analytics.history.trends import batting_trend, bowling_trend, team_trend
from app.core.exceptions import (
    AIGroundingFailedError,
    AIInvalidResponseError,
    AppError,
    PlayerNotFoundError,
    TeamNotFoundError,
)
from app.core.logging import get_logger
from app.models.player import Player
from app.models.team import Team
from app.repositories.historical_stats import HistoricalStatsRepository
from app.schemas.analytics import (
    HistoricalClarificationOption,
    HistoricalEvidence,
    HistoricalQueryResponse,
    HistoricalScopeOut,
    PlayerAnalyticsResponse,
)
from app.services.historical_stats import HistoricalStatsService, _scope_out

logger = get_logger(__name__)


class HistoricalIntelligenceService:
    def __init__(
        self,
        *,
        stats: HistoricalStatsService,
        repository: HistoricalStatsRepository,
        router: HistoricalQuestionRouter,
        prompts: HistoricalPromptBuilder,
        ai: AIService,
        grounding: HistoricalGroundingValidator,
        max_retries: int = 1,
    ) -> None:
        self._stats = stats
        self._repo = repository
        self._router = router
        self._prompts = prompts
        self._ai = ai
        self._grounding = grounding
        self._max_retries = max_retries

    async def query(self, user_id: uuid.UUID, question: str) -> HistoricalQueryResponse:
        intent = self._router.classify(question)
        if intent.season_clarification:
            return _clarification(
                "What date range should I use for this season?",
                intent,
                [],
            )
        if intent.out_of_scope:
            return HistoricalQueryResponse(
                content=(
                    "I can answer questions about your completed matches — player stats, "
                    "team records, form, comparisons, and trends in that history."
                ),
                answer_type=HistoricalAnswerType.OUT_OF_SCOPE.value,
                question_type=intent.type.value,
                follow_up_suggestions=[
                    "Who has scored the most runs?",
                    "What is the team's win rate?",
                ],
            )
        players = await self._repo.list_owned_players(user_id)
        teams = await self._repo.list_owned_teams(user_id)
        resolution = resolve_historical_entities(question, intent, players, teams)
        if resolution.needs_player_clarification:
            names = [item.name for item in resolution.ambiguous_players]
            options = [
                HistoricalClarificationOption(label=item.name, message=f"I mean {item.name}.")
                for item in resolution.ambiguous_players
            ]
            return _clarification(
                "I found more than one matching player: " + " and ".join(names) + ". Which one do you mean?",
                intent,
                options,
            )
        if resolution.needs_team_clarification:
            team_options = resolution.ambiguous_teams or [NamedEntity(item.id, item.name) for item in teams[:6]]
            labels = [item.name for item in team_options]
            return _clarification(
                "Which team do you mean — " + " or ".join(labels) + "?",
                intent,
                [
                    HistoricalClarificationOption(label=item.name, message=f"I mean {item.name}.")
                    for item in team_options
                ],
            )
        if resolution.missing_player and _needs_named_player(intent):
            return HistoricalQueryResponse(
                content=f"I couldn't find a player named {resolution.missing_player} in your cricket data.",
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
            )
        scope = HistoricalScope(format=intent.format, last_n=intent.last_n).normalized()
        try:
            return await self._answer(user_id, question, intent, resolution, scope, players, teams)
        except AppError as exc:
            if exc.code in {
                "AI_PROVIDER_ERROR",
                "AI_TIMEOUT",
                "AI_INVALID_RESPONSE",
                "AI_GROUNDING_FAILED",
                "AI_DISABLED",
            }:
                logger.info(
                    "historical_query_failed",
                    user_id=str(user_id),
                    question_type=intent.type.value,
                    status=exc.code,
                    used_ai=True,
                )
                return HistoricalQueryResponse(
                    content=(
                        "I couldn't generate the AI explanation right now. "
                        "The underlying stats are still available on the Stats screens."
                    ),
                    answer_type=HistoricalAnswerType.ANALYTICAL.value,
                    question_type=intent.type.value,
                    used_ai=True,
                    generation_error={"code": exc.code, "message": exc.message},
                )
            raise

    async def _answer(
        self,
        user_id: uuid.UUID,
        question: str,
        intent: HistoricalIntent,
        resolution: HistoricalResolution,
        scope: HistoricalScope,
        players: list[Player],
        teams: list[Team],
    ) -> HistoricalQueryResponse:
        if intent.type is HistoricalQuestionType.PLAYER_RANKING:
            metric = intent.ranking_metric or "runs"
            board = await self._stats.leaderboards(user_id, metric=metric, scope=scope, limit=5, offset=0)
            if not board.items:
                content = "There are not enough completed-match samples for that ranking yet."
            else:
                top = board.items[0]
                tied = [item for item in board.items if item.value == top.value]
                names = ", ".join(item.name for item in tied)
                content = f"{names} lead for {metric.replace('_', ' ')} at {top.value}."
                if board.qualification:
                    content += f" {board.qualification}."
            logger.info("historical_query", user_id=str(user_id), question_type=intent.type.value, used_ai=False)
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=board.scope,
                used_ai=False,
                follow_up_suggestions=["Who has taken the most wickets?"],
            )

        if intent.type in {
            HistoricalQuestionType.PLAYER_STATS,
            HistoricalQuestionType.PLAYER_FORM,
            HistoricalQuestionType.DIRECT_HISTORICAL_STAT,
        }:
            player = await self._player(user_id, resolution, players)
            payload = await self._stats.player_stats(user_id, player.id, scope)
            content = _player_direct(payload, intent)
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=payload.scope,
                evidence=_player_evidence(payload),
                used_ai=False,
                facts={"batting": payload.batting.model_dump(), "bowling": payload.bowling.model_dump()},
                follow_up_suggestions=["How has their form changed?", "Who has scored the most runs?"],
            )

        if intent.type is HistoricalQuestionType.TEAM_STATS:
            team = await self._team(user_id, resolution, teams)
            team_payload = await self._stats.team_stats(user_id, team.id, scope)
            win = "n/a" if team_payload.win_percentage is None else str(team_payload.win_percentage)
            content = (
                f"{team_payload.name} have won {team_payload.wins} of {team_payload.matches} "
                f"completed matches, a win rate of {win}%."
            )
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=team_payload.scope,
                used_ai=False,
                facts={"team": team_payload.model_dump(mode="json")},
            )

        if intent.type is HistoricalQuestionType.TEAM_FORM and not intent.requires_llm:
            team = await self._team(user_id, resolution, teams)
            team_form = await self._stats.team_stats(user_id, team.id, scope)
            form = " ".join(team_form.recent_form) or "no completed results"
            content = f"In {team_form.name}'s last {len(team_form.recent_form) or RECENT_APPEARANCES} matches: {form}."
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=team_form.scope,
                used_ai=False,
            )

        if intent.type is HistoricalQuestionType.PLAYER_COMPARISON and not intent.requires_llm:
            left, right = await self._two_players(user_id, resolution, players)
            compared = await self._stats.compare_players(user_id, left.id, right.id, scope)
            content = _compare_direct(compared.player_a, compared.player_b, compared.note)
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=compared.scope,
                used_ai=False,
                facts={"player_a": compared.player_a.model_dump(), "player_b": compared.player_b.model_dump()},
            )

        if intent.type is HistoricalQuestionType.TEAM_COMPARISON and not intent.requires_llm:
            left, right = await self._two_teams(user_id, resolution, teams)
            team_compared = await self._stats.compare_teams(user_id, left.id, right.id, scope)
            h2h = team_compared.head_to_head
            content = (
                f"{team_compared.team_a.name} {team_compared.team_a.win_percentage}% win rate vs "
                f"{team_compared.team_b.name} {team_compared.team_b.win_percentage}%. "
                f"Head-to-head: {h2h.matches} matches, {team_compared.team_a.name} {h2h.team_a_wins}, "
                f"{team_compared.team_b.name} {h2h.team_b_wins}, {h2h.ties} ties."
            )
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=team_compared.scope,
                used_ai=False,
            )

        if intent.type is HistoricalQuestionType.HEAD_TO_HEAD:
            left, right = await self._two_teams(user_id, resolution, teams)
            h2h_compared = await self._stats.compare_teams(user_id, left.id, right.id, scope)
            h2h = h2h_compared.head_to_head
            content = (
                f"{h2h_compared.team_a.name} vs {h2h_compared.team_b.name}: "
                f"{h2h.matches} completed matches, "
                f"{h2h_compared.team_a.name} {h2h.team_a_wins} wins, "
                f"{h2h_compared.team_b.name} {h2h.team_b_wins} wins, {h2h.ties} ties."
            )
            return HistoricalQueryResponse(
                content=content,
                answer_type=HistoricalAnswerType.DIRECT_STAT.value,
                question_type=intent.type.value,
                scope=h2h_compared.scope,
                used_ai=False,
            )

        return await self._analytical(user_id, question, intent, resolution, scope, players, teams)

    async def _analytical(
        self,
        user_id: uuid.UUID,
        question: str,
        intent: HistoricalIntent,
        resolution: HistoricalResolution,
        scope: HistoricalScope,
        players: list[Player],
        teams: list[Team],
    ) -> HistoricalQueryResponse:
        package = await self._fact_package(user_id, intent, resolution, scope, players, teams)
        system_prompt, user_prompt = self._prompts.build(question=question, facts=package)
        last_error: Exception | None = None
        for _ in range(self._max_retries + 1):
            try:
                generation = await self._ai.generate_structured(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=StructuredHistoricalInsight,
                )
                self._grounding.validate(generation.data, package)
                evidence = [
                    HistoricalEvidence(
                        fact_id=item["id"], type=item["type"], label=item["label"], summary=item["summary"]
                    )
                    for item in package.get("facts", [])
                    if item["id"] in set(generation.data.fact_ids)
                ]
                content = generation.data.summary
                if generation.data.insights:
                    content += "\n\n" + "\n".join(f"• {item}" for item in generation.data.insights)
                logger.info(
                    "historical_query",
                    user_id=str(user_id),
                    question_type=intent.type.value,
                    used_ai=True,
                    provider=generation.provider,
                    model=generation.model,
                    latency_ms=generation.latency_ms,
                    input_tokens=generation.input_tokens,
                    output_tokens=generation.output_tokens,
                )
                return HistoricalQueryResponse(
                    content=content,
                    answer_type=HistoricalAnswerType.ANALYTICAL.value,
                    question_type=intent.type.value,
                    scope=HistoricalScopeOut.model_validate(package["scope"]) if package.get("scope") else None,
                    evidence=evidence,
                    used_ai=True,
                    facts=package,
                    follow_up_suggestions=generation.data.caveats[:3],
                )
            except (AIInvalidResponseError, AIGroundingFailedError) as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    async def _fact_package(
        self,
        user_id: uuid.UUID,
        intent: HistoricalIntent,
        resolution: HistoricalResolution,
        scope: HistoricalScope,
        players: list[Player],
        teams: list[Team],
    ) -> dict[str, Any]:
        facts: list[dict] = []
        player_ids: list[str] = []
        team_ids: list[str] = []
        allowed: set[str] = set()
        scope_out: HistoricalScopeOut | None = None
        if resolution.players:
            player = next(item for item in players if item.id == resolution.players[0].id)
            payload = await self._stats.player_stats(user_id, player.id, scope)
            scope_out = payload.scope
            player_ids.append(str(player.id))
            batting_rows = await self._repo.batting_rows(
                user_id,
                player.id,
                [item.match_id for item in await self._repo.player_appearances(user_id, player.id, scope)],
            )
            bowling_rows = await self._repo.bowling_rows(
                user_id,
                player.id,
                [item.match_id for item in await self._repo.player_appearances(user_id, player.id, scope)],
            )
            for window in batting_trend(batting_rows) + bowling_trend(bowling_rows):
                fact_id = f"player_{player.id.hex[:8]}_{window.metric}"
                facts.append(
                    {
                        "id": fact_id,
                        "type": "trend",
                        "label": window.metric,
                        "summary": (
                            f"{window.metric}: last {RECENT_APPEARANCES}={window.last_n}, "
                            f"previous={window.previous_n}, delta={window.delta}, "
                            f"n={window.sample_last}/{window.sample_previous}"
                        ),
                    }
                )
                for value in (
                    window.last_n,
                    window.previous_n,
                    window.delta,
                    window.sample_last,
                    window.sample_previous,
                ):
                    if value is not None:
                        allowed.add(str(int(value)) if float(value).is_integer() else str(value))
            facts.append(
                {
                    "id": f"player_{player.id.hex[:8]}_batting",
                    "type": "batting",
                    "label": player.name,
                    "summary": (
                        f"{player.name}: {payload.batting.runs} runs, avg {payload.batting.batting_average}, "
                        f"SR {payload.batting.strike_rate}, {payload.batting.innings} innings"
                    ),
                }
            )
        if resolution.teams or intent.type in {
            HistoricalQuestionType.TEAM_FORM,
            HistoricalQuestionType.HISTORICAL_TREND,
        }:
            team = None
            if resolution.teams:
                team = next(item for item in teams if item.id == resolution.teams[0].id)
            elif teams:
                team = teams[0]
            if team is not None:
                team_payload = await self._stats.team_stats(user_id, team.id, scope)
                scope_out = team_payload.scope
                team_ids.append(str(team.id))
                rows = await self._repo.team_matches(user_id, team.id, scope)
                for window in team_trend(rows):
                    fact_id = f"team_{team.id.hex[:8]}_{window.metric}"
                    facts.append(
                        {
                            "id": fact_id,
                            "type": "trend",
                            "label": window.metric,
                            "summary": (
                                f"{team.name} {window.metric}: last={window.last_n}, previous={window.previous_n}, "
                                f"delta={window.delta}"
                            ),
                        }
                    )
                facts.append(
                    {
                        "id": f"team_{team.id.hex[:8]}_record",
                        "type": "team",
                        "label": team.name,
                        "summary": (
                            f"{team.name}: {team_payload.wins}/{team_payload.matches} wins, "
                            f"win% {team_payload.win_percentage}, form {' '.join(team_payload.recent_form)}"
                        ),
                    }
                )
                if intent.unavailable_topic == "death_overs" or intent.type is HistoricalQuestionType.HISTORICAL_TREND:
                    phase_rows = await self._repo.closing_phase_runs(
                        user_id,
                        team.id,
                        [item.match_id for item in rows[:RECENT_APPEARANCES]],
                    )
                    closing = aggregate_closing_phase(phase_rows)
                    if closing is None:
                        facts.append(
                            {
                                "id": f"team_{team.id.hex[:8]}_closing_unsupported",
                                "type": "scope",
                                "label": "Closing phase",
                                "summary": (
                                    "Closing-phase (death-over) trends are unavailable for this format "
                                    "or sample; no phase ranges were invented."
                                ),
                            }
                        )
                    else:
                        fact_id = f"team_{team.id.hex[:8]}_closing"
                        facts.append(
                            {
                                "id": fact_id,
                                "type": "trend",
                                "label": "Closing phase",
                                "summary": (
                                    f"{team.name} closing-phase runs across {closing['matches']} recent matches: "
                                    f"{closing['runs']} total, average {closing['average_runs']}."
                                ),
                            }
                        )
                        allowed.add(str(closing["runs"]))
                        allowed.add(str(closing["average_runs"]))
                        allowed.add(str(closing["matches"]))
        if not facts:
            facts.append(
                {"id": "empty", "type": "scope", "label": "No facts", "summary": "No historical facts in scope."}
            )
        return {
            "scope": scope_out.model_dump(mode="json") if scope_out else _scope_out(scope, 0).model_dump(mode="json"),
            "facts": facts,
            "fact_index": [{"id": item["id"], "type": item["type"], "label": item["label"]} for item in facts],
            "player_ids": player_ids,
            "team_ids": team_ids,
            "allowed_numbers": sorted(allowed),
        }

    async def _player(self, user_id: uuid.UUID, resolution: HistoricalResolution, players: list[Player]) -> Player:
        if resolution.players:
            found = await self._repo.player_owned(resolution.players[0].id, user_id)
            if found:
                return found
        if len(players) == 1:
            return players[0]
        raise _missing_player()

    async def _team(self, user_id: uuid.UUID, resolution: HistoricalResolution, teams: list[Team]) -> Team:
        if resolution.teams:
            found = await self._repo.team_owned(resolution.teams[0].id, user_id)
            if found:
                return found
        if len(teams) == 1:
            return teams[0]
        raise TeamNotFoundError()

    async def _two_players(self, user_id: uuid.UUID, resolution: HistoricalResolution, players: list[Player]):
        if len(resolution.players) >= 2:
            left = await self._repo.player_owned(resolution.players[0].id, user_id)
            right = await self._repo.player_owned(resolution.players[1].id, user_id)
            if left and right:
                return left, right
        raise _missing_player()

    async def _two_teams(self, user_id: uuid.UUID, resolution: HistoricalResolution, teams: list[Team]):
        if len(resolution.teams) >= 2:
            left = await self._repo.team_owned(resolution.teams[0].id, user_id)
            right = await self._repo.team_owned(resolution.teams[1].id, user_id)
            if left and right:
                return left, right
        raise TeamNotFoundError()


def _needs_named_player(intent: HistoricalIntent) -> bool:
    return intent.type in {
        HistoricalQuestionType.PLAYER_STATS,
        HistoricalQuestionType.PLAYER_FORM,
        HistoricalQuestionType.PLAYER_COMPARISON,
    }


def _missing_player() -> PlayerNotFoundError:
    return PlayerNotFoundError()


def _clarification(
    content: str, intent: HistoricalIntent, options: list[HistoricalClarificationOption]
) -> HistoricalQueryResponse:
    return HistoricalQueryResponse(
        content=content,
        answer_type=HistoricalAnswerType.CLARIFICATION.value,
        question_type=intent.type.value,
        clarification_options=options,
        used_ai=False,
    )


def _player_direct(payload: PlayerAnalyticsResponse, intent: HistoricalIntent) -> str:
    batting = payload.batting
    bowling = payload.bowling
    if intent.type is HistoricalQuestionType.PLAYER_FORM:
        scores = ", ".join(item.display or "—" for item in payload.recent_form) or "no batting innings"
        return f"In {payload.name}'s last {len(payload.recent_form) or RECENT_APPEARANCES} matches: {scores}."
    avg = "not applicable" if batting.batting_average is None else str(batting.batting_average)
    line = (
        f"{payload.name} has scored {batting.runs} runs in {batting.innings} innings "
        f"at an average of {avg} and strike rate of {batting.strike_rate}."
    )
    if bowling.innings_bowled:
        bowl_avg = "not available" if bowling.bowling_average is None else str(bowling.bowling_average)
        line += f" Bowling: {bowling.wickets} wickets, average {bowl_avg}."
    return line


def _compare_direct(left: PlayerAnalyticsResponse, right: PlayerAnalyticsResponse, note: str | None) -> str:
    text = (
        f"{left.name}: {left.batting.runs} runs, avg {left.batting.batting_average}, "
        f"SR {left.batting.strike_rate}. "
        f"{right.name}: {right.batting.runs} runs, avg {right.batting.batting_average}, "
        f"SR {right.batting.strike_rate}."
    )
    if note:
        text += f" {note}"
    return text


def _player_evidence(payload: PlayerAnalyticsResponse) -> list[HistoricalEvidence]:
    batting = payload.batting
    return [
        HistoricalEvidence(
            fact_id=f"player_{payload.player_id.hex[:8]}_batting",
            type="batting",
            label="Batting",
            summary=f"{batting.runs} runs · {batting.innings} innings · avg {batting.batting_average}",
        )
    ]
