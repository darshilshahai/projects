import logging

from openai import APIError, APITimeoutError, AsyncOpenAI

from app.core.config import get_openai_client, get_settings
from app.models.response import AnalyzeResponse, IdeaAnalysisOutput
from app.prompts.analysis_prompt import ANALYSIS_INSTRUCTIONS, build_analysis_input
from app.services.competitor_research import CompetitorResearchResult
from app.services.openai_errors import analysis_error_message, log_openai_failure

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    pass


def _format_competitors_for_analysis(research: CompetitorResearchResult) -> str:
    if not research.competitors:
        return "No competitors were identified."

    lines: list[str] = []
    for index, competitor in enumerate(research.competitors, start=1):
        url_text = competitor.url or "No verified URL"
        lines.append(
            f"{index}. {competitor.name}\n"
            f"Description: {competitor.description}\n"
            f"Verified URL: {url_text}"
        )
    return "\n\n".join(lines)


async def analyze_idea(
    idea: str,
    context: str | None,
    research: CompetitorResearchResult,
    client: AsyncOpenAI | None = None,
) -> AnalyzeResponse:
    logger.info("startup analysis started")

    openai_client = client or get_openai_client()
    settings = get_settings()

    try:
        response = await openai_client.responses.parse(
            model=settings.analysis_model,
            instructions=ANALYSIS_INSTRUCTIONS,
            input=build_analysis_input(
                idea=idea,
                context=context,
                research_summary=research.research_summary,
                competitors_text=_format_competitors_for_analysis(research),
            ),
            text_format=IdeaAnalysisOutput,
            store=False,
        )
    except (APIError, APITimeoutError) as exc:
        log_openai_failure(logger, "startup analysis", exc)
        raise AnalysisError(analysis_error_message(exc)) from exc

    parsed = response.output_parsed
    if parsed is None:
        logger.error("startup analysis returned no structured output")
        raise AnalysisError("Unable to analyze this idea right now. Please try again.")

    logger.info("startup analysis completed")

    return AnalyzeResponse(
        idea_summary=parsed.idea_summary,
        target_user=parsed.target_user,
        problem=parsed.problem,
        market_saturation=parsed.market_saturation,
        competitors=research.competitors,
        biggest_problem=parsed.biggest_problem,
        differentiation=parsed.differentiation,
        recommended_wedge=parsed.recommended_wedge,
        mvp=parsed.mvp,
        scores=parsed.scores,
        verdict=parsed.verdict,
        confidence=parsed.confidence,
        reason=parsed.reason,
    )
