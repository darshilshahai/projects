import logging

from openai import APIError, APITimeoutError, RateLimitError

RESEARCH_UNAVAILABLE = (
    "Market research is temporarily unavailable. Please try again later."
)
ANALYSIS_UNAVAILABLE = (
    "Unable to analyze this idea right now. Please try again later."
)


def _error_payload(exc: APIError) -> dict:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return error
    return {}


def is_quota_exhausted(exc: APIError) -> bool:
    payload = _error_payload(exc)
    return payload.get("code") == "credit_balance_exhausted" or payload.get(
        "type"
    ) == "insufficient_quota"


def log_openai_failure(logger: logging.Logger, operation: str, exc: Exception) -> None:
    if isinstance(exc, APITimeoutError):
        logger.warning("%s timed out", operation)
        return

    if isinstance(exc, RateLimitError) and is_quota_exhausted(exc):
        logger.error("%s failed: OpenAI account has no remaining credits", operation)
        return

    if isinstance(exc, RateLimitError):
        logger.warning("%s failed: OpenAI rate limit reached", operation)
        return

    if isinstance(exc, APIError):
        status_code = getattr(exc, "status_code", "unknown")
        logger.warning("%s failed: OpenAI API error status=%s", operation, status_code)
        return

    logger.exception("%s failed", operation)


def research_error_message(exc: Exception) -> str:
    return RESEARCH_UNAVAILABLE


def analysis_error_message(exc: Exception) -> str:
    return ANALYSIS_UNAVAILABLE
