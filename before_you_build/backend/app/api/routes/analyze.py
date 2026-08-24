import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.services.competitor_research import ResearchError, research_competitors
from app.services.idea_analyzer import AnalysisError, analyze_idea

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_startup_idea(
    payload: AnalyzeRequest,
    request: Request,
) -> AnalyzeResponse:
    request_id = str(uuid.uuid4())[:8]
    started = time.perf_counter()
    logger.info("analysis request started request_id=%s", request_id)

    try:
        logger.info("competitor research started request_id=%s", request_id)
        research = await research_competitors(
            idea=payload.idea,
            context=payload.context,
        )
        logger.info("competitor research completed request_id=%s", request_id)

        logger.info("startup analysis started request_id=%s", request_id)
        result = await analyze_idea(
            idea=payload.idea,
            context=payload.context,
            research=research,
        )
        elapsed = time.perf_counter() - started
        logger.info(
            "startup analysis completed request_id=%s duration=%.1fs status=200",
            request_id,
            elapsed,
        )
        return result
    except ResearchError as exc:
        elapsed = time.perf_counter() - started
        logger.warning(
            "request failed during competitor research request_id=%s duration=%.1fs status=502",
            request_id,
            elapsed,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except AnalysisError as exc:
        elapsed = time.perf_counter() - started
        logger.warning(
            "request failed during startup analysis request_id=%s duration=%.1fs status=502",
            request_id,
            elapsed,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception(
            "request failed request_id=%s duration=%.1fs status=500",
            request_id,
            elapsed,
        )
        raise HTTPException(status_code=500, detail="Unexpected server error.")
