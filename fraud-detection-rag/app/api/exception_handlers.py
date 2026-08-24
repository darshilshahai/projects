from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.dependencies import ApplicationDependencyError
from app.ingestion.pipeline import ChunkingPipelineError
from app.services.rag_service import RAGServiceError


logger = logging.getLogger(__name__)


def create_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    """
    Create one consistent API error structure.
    """

    content: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }

    if details is not None:
        content["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


async def application_dependency_error_handler(
    request: Request,
    exc: ApplicationDependencyError,
) -> JSONResponse:
    """
    Handle missing application services.
    """

    logger.exception(
        "Application dependency error",
        extra={
            "path": request.url.path,
        },
    )

    return create_error_response(
        status_code=503,
        code="SERVICE_NOT_READY",
        message=str(exc),
    )


async def chunking_pipeline_error_handler(
    request: Request,
    exc: ChunkingPipelineError,
) -> JSONResponse:
    """
    Handle document chunking and ingestion failures.
    """

    logger.exception(
        "Chunking pipeline failure",
        extra={
            "path": request.url.path,
        },
    )

    return create_error_response(
        status_code=422,
        code="DOCUMENT_PROCESSING_FAILED",
        message=str(exc),
    )


async def rag_service_error_handler(
    request: Request,
    exc: RAGServiceError,
) -> JSONResponse:
    """
    Handle retrieval or LLM generation failures.
    """

    logger.exception(
        "RAG service failure",
        extra={
            "path": request.url.path,
        },
    )

    return create_error_response(
        status_code=500,
        code="RAG_SERVICE_FAILED",
        message=str(exc),
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """
    Handle validation errors raised inside application services.
    """

    return create_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="The supplied data is invalid.",
        details=exc.errors(),
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected server errors.

    Internal exception details are logged but are not returned to clients.
    """

    logger.exception(
        "Unexpected application error",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred.",
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register application exception handlers.
    """

    app.add_exception_handler(
        ApplicationDependencyError,
        cast(Any, application_dependency_error_handler),
    )

    app.add_exception_handler(
        ChunkingPipelineError,
        cast(Any, chunking_pipeline_error_handler),
    )

    app.add_exception_handler(
        RAGServiceError,
        cast(Any, rag_service_error_handler),
    )

    app.add_exception_handler(
        ValidationError,
        cast(Any, pydantic_validation_error_handler),
    )

    app.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )
