from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.match_context_builder import MatchContextBuilder
from app.ai.prompts.historical_prompt import HistoricalPromptBuilder
from app.ai.prompts.match_analysis_prompt import MatchAnalysisPromptBuilder
from app.ai.prompts.match_chat_prompt import MatchChatPromptBuilder
from app.ai.providers.base import AIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.routing.historical_router import HistoricalQuestionRouter
from app.ai.routing.question_router import MatchQuestionRouter
from app.ai.services.ai_service import AIService
from app.ai.services.chat_grounding import ChatGroundingValidator
from app.ai.services.grounding import GroundingValidator
from app.ai.services.historical_grounding import HistoricalGroundingValidator
from app.ai.services.historical_intelligence_service import HistoricalIntelligenceService
from app.ai.services.match_analysis_service import MatchAnalysisService
from app.ai.services.match_chat_service import MatchChatService
from app.core.config import Settings, get_settings
from app.core.exceptions import InvalidTokenError
from app.core.security import bearer_scheme
from app.db.session import get_db
from app.models.user import User
from app.repositories.ai_chat import AIConversationRepository, AIMessageRepository
from app.repositories.historical_stats import HistoricalStatsRepository
from app.repositories.match_analysis import MatchAnalysisRepository
from app.services.auth_service import AuthService
from app.services.historical_stats import HistoricalStatsService
from app.services.match import MatchService
from app.services.player import PlayerService
from app.services.roster import RosterService
from app.services.scorecard import ScorecardService
from app.services.scoring import ScoringService
from app.services.team import TeamService


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(session, settings)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise InvalidTokenError("Missing access token.")
    return await auth.get_current_user(credentials.credentials)


def client_user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    if value is None:
        return None
    return value[:512]


def get_team_service(session: Annotated[AsyncSession, Depends(get_db)]) -> TeamService:
    return TeamService(session)


def get_player_service(session: Annotated[AsyncSession, Depends(get_db)]) -> PlayerService:
    return PlayerService(session)


def get_roster_service(session: Annotated[AsyncSession, Depends(get_db)]) -> RosterService:
    return RosterService(session)


def get_match_service(session: Annotated[AsyncSession, Depends(get_db)]) -> MatchService:
    return MatchService(session)


def get_scoring_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ScoringService:
    return ScoringService(session)


def get_scorecard_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ScorecardService:
    return ScorecardService(session)


def get_ai_provider(settings: Annotated[Settings, Depends(get_settings)]) -> AIProvider:
    return OpenAIProvider(settings)


def get_ai_service(
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AIService:
    return AIService(provider, settings)


def get_match_analysis_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    matches: Annotated[MatchService, Depends(get_match_service)],
    scorecards: Annotated[ScorecardService, Depends(get_scorecard_service)],
    ai: Annotated[AIService, Depends(get_ai_service)],
) -> MatchAnalysisService:
    return MatchAnalysisService(
        matches=matches,
        analyses=MatchAnalysisRepository(session),
        context=MatchContextBuilder(matches, scorecards),
        prompts=MatchAnalysisPromptBuilder(),
        ai=ai,
        grounding=GroundingValidator(),
        max_retries=settings.ai_max_retries,
    )


def get_historical_stats_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> HistoricalStatsService:
    return HistoricalStatsService(HistoricalStatsRepository(session))


def get_historical_intelligence_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    ai: Annotated[AIService, Depends(get_ai_service)],
) -> HistoricalIntelligenceService:
    repository = HistoricalStatsRepository(session)
    return HistoricalIntelligenceService(
        stats=HistoricalStatsService(repository),
        repository=repository,
        router=HistoricalQuestionRouter(),
        prompts=HistoricalPromptBuilder(),
        ai=ai,
        grounding=HistoricalGroundingValidator(),
        max_retries=settings.ai_max_retries,
    )


def get_match_chat_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    matches: Annotated[MatchService, Depends(get_match_service)],
    scorecards: Annotated[ScorecardService, Depends(get_scorecard_service)],
    ai: Annotated[AIService, Depends(get_ai_service)],
) -> MatchChatService:
    return MatchChatService(
        matches=matches,
        conversations=AIConversationRepository(session),
        messages=AIMessageRepository(session),
        context=MatchContextBuilder(matches, scorecards),
        router=MatchQuestionRouter(),
        prompts=MatchChatPromptBuilder(),
        ai=ai,
        grounding=ChatGroundingValidator(),
        max_retries=settings.ai_max_retries,
    )
