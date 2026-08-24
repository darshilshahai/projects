import logging
import re
from urllib.parse import urlparse

from openai import APIError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, Field

from app.core.config import get_openai_client, get_settings
from app.models.response import Competitor
from app.prompts.research_prompt import RESEARCH_INSTRUCTIONS, build_research_input
from app.services.openai_errors import log_openai_failure, research_error_message

logger = logging.getLogger(__name__)


class ResearchError(Exception):
    pass


class ResearchCompetitorDraft(BaseModel):
    name: str
    description: str
    cited_url: str | None = None


class ResearchStructuredOutput(BaseModel):
    research_summary: str
    competitors: list[ResearchCompetitorDraft] = Field(min_length=1, max_length=8)


class CompetitorResearchResult(BaseModel):
    research_summary: str
    competitors: list[Competitor]
    verified_source_urls: list[str]


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def extract_verified_source_urls(response) -> list[str]:
    urls: set[str] = set()

    for item in response.output:
        if item.type == "web_search_call":
            action = item.action
            if action.type == "search" and action.sources:
                for source in action.sources:
                    if source.url:
                        urls.add(source.url.strip())
            elif action.type == "open_page" and action.url:
                urls.add(action.url.strip())
            elif action.type == "find_in_page" and action.url:
                urls.add(action.url.strip())
        elif item.type == "message":
            for content in item.content:
                if content.type != "output_text":
                    continue
                annotations = getattr(content, "annotations", None) or []
                for annotation in annotations:
                    if getattr(annotation, "type", None) == "url_citation" and annotation.url:
                        urls.add(annotation.url.strip())

    return sorted(urls)


def _resolve_verified_url(
    candidate: str | None,
    verified_urls: list[str],
) -> str | None:
    if not candidate:
        return None

    normalized_candidate = _normalize_url(candidate)
    for url in verified_urls:
        if _normalize_url(url) == normalized_candidate:
            return url
    return None


def _normalize_competitor_name(name: str) -> str:
    cleaned = name.strip().lower()
    for prefix in ("openai ", "google ", "microsoft ", "adobe "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return re.sub(r"[^a-z0-9]+", "", cleaned)


def _dedupe_competitors(competitors: list[Competitor]) -> list[Competitor]:
    seen_names: set[str] = set()
    seen_domains: set[str] = set()
    deduped: list[Competitor] = []

    for competitor in competitors:
        normalized_name = _normalize_competitor_name(competitor.name)
        domain = ""
        if competitor.url:
            domain = urlparse(competitor.url).netloc.lower().replace("www.", "")

        if normalized_name in seen_names:
            continue
        if domain and domain in seen_domains:
            continue

        seen_names.add(normalized_name)
        if domain:
            seen_domains.add(domain)

        deduped.append(competitor)

    return deduped


def _build_competitors(
    drafts: list[ResearchCompetitorDraft],
    verified_urls: list[str],
) -> list[Competitor]:
    competitors: list[Competitor] = []

    for draft in drafts:
        url = _resolve_verified_url(draft.cited_url, verified_urls)

        competitors.append(
            Competitor(
                name=draft.name.strip(),
                description=draft.description.strip(),
                url=url,
            )
        )

    return _dedupe_competitors(competitors)


async def research_competitors(
    idea: str,
    context: str | None,
    client: AsyncOpenAI | None = None,
) -> CompetitorResearchResult:
    logger.info("competitor research started")

    openai_client = client or get_openai_client()
    settings = get_settings()

    try:
        response = await openai_client.responses.parse(
            model=settings.research_model,
            instructions=RESEARCH_INSTRUCTIONS,
            input=build_research_input(idea, context),
            tools=[{"type": "web_search", "search_context_size": "medium"}],
            include=["web_search_call.action.sources"],
            text_format=ResearchStructuredOutput,
            store=False,
        )
    except (APIError, APITimeoutError) as exc:
        log_openai_failure(logger, "competitor research", exc)
        raise ResearchError(research_error_message(exc)) from exc

    parsed = response.output_parsed
    if parsed is None:
        logger.error("competitor research returned no structured output")
        raise ResearchError("Unable to research this idea right now. Please try again.")

    verified_urls = extract_verified_source_urls(response)
    competitors = _build_competitors(parsed.competitors, verified_urls)

    logger.info("competitor research completed")

    return CompetitorResearchResult(
        research_summary=parsed.research_summary.strip(),
        competitors=competitors,
        verified_source_urls=verified_urls,
    )
