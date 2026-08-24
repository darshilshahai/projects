from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class ResourceNotFoundError(AppError):
    def __init__(
        self,
        message: str = "The requested resource was not found.",
        *,
        code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(code=code, message=message, status_code=404)


class TeamNotFoundError(ResourceNotFoundError):
    def __init__(self) -> None:
        super().__init__("Team not found.", code="TEAM_NOT_FOUND")


class PlayerNotFoundError(ResourceNotFoundError):
    def __init__(self) -> None:
        super().__init__("Player not found.", code="PLAYER_NOT_FOUND")


class PlayerNotInTeamError(ResourceNotFoundError):
    def __init__(self) -> None:
        super().__init__("This player is not on the team roster.", code="PLAYER_NOT_IN_TEAM")


class ConflictError(AppError):
    def __init__(
        self,
        message: str = "The request conflicts with existing data.",
        *,
        code: str = "CONFLICT",
    ) -> None:
        super().__init__(code=code, message=message, status_code=409)


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            "An account with this email already exists.",
            code="EMAIL_ALREADY_REGISTERED",
        )


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            status_code=401,
        )


class InvalidTokenError(AppError):
    def __init__(self, message: str = "Invalid token.") -> None:
        super().__init__(code="INVALID_TOKEN", message=message, status_code=401)


class TokenExpiredError(AppError):
    def __init__(self, message: str = "The token has expired.") -> None:
        super().__init__(code="TOKEN_EXPIRED", message=message, status_code=401)


class SessionRevokedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="SESSION_REVOKED",
            message="This session is no longer valid.",
            status_code=401,
        )


class AccountInactiveError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="ACCOUNT_INACTIVE",
            message="This account is currently inactive.",
            status_code=403,
        )


class TeamNameAlreadyExistsError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            "You already have a team with this name.",
            code="TEAM_NAME_ALREADY_EXISTS",
        )


class PlayerAlreadyInTeamError(ConflictError):
    def __init__(self) -> None:
        super().__init__(
            "This player is already in the roster.",
            code="PLAYER_ALREADY_IN_TEAM",
        )


class InactiveTeamError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="INACTIVE_TEAM",
            message="This team is currently inactive.",
            status_code=409,
        )


class InactivePlayerError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="INACTIVE_PLAYER",
            message="This player is currently inactive.",
            status_code=409,
        )


class MatchNotFoundError(ResourceNotFoundError):
    def __init__(self) -> None:
        super().__init__("Match not found.", code="MATCH_NOT_FOUND")


class MatchNotEditableError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="MATCH_NOT_EDITABLE",
            message="This match can no longer be configured.",
            status_code=409,
        )


class InvalidDateRangeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="INVALID_DATE_RANGE",
            message="date_from must be before or equal to date_to.",
            status_code=400,
        )


class InvalidMatchFormatError(AppError):
    def __init__(self, message: str = "This match format is not supported.") -> None:
        super().__init__(code="INVALID_MATCH_FORMAT", message=message, status_code=400)


class InvalidOversError(AppError):
    def __init__(self, message: str = "Overs per innings must be between 1 and 50.") -> None:
        super().__init__(code="INVALID_OVERS", message=message, status_code=400)


class SameTeamSelectedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="SAME_TEAM_SELECTED",
            message="Choose two different teams.",
            status_code=409,
        )


class PlayerNotInRosterError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="PLAYER_NOT_IN_ROSTER",
            message="That player is not on this team's active roster.",
            status_code=409,
        )


class InvalidPlayingXiSizeError(AppError):
    def __init__(self, message: str = "Playing XI size is invalid.") -> None:
        super().__init__(code="INVALID_PLAYING_XI_SIZE", message=message, status_code=409)


class DuplicatePlayingXiPlayerError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="DUPLICATE_PLAYING_XI_PLAYER",
            message="A player can only appear once in a match.",
            status_code=409,
        )


class CaptainNotInXiError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="CAPTAIN_NOT_IN_XI",
            message="The captain must be in the Playing XI.",
            status_code=409,
        )


class KeeperNotInXiError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="KEEPER_NOT_IN_XI",
            message="The wicketkeeper must be in the Playing XI.",
            status_code=409,
        )


class TossTeamInvalidError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="TOSS_TEAM_INVALID",
            message="Toss winner must be one of the match teams.",
            status_code=409,
        )


class MatchNotReadyError(AppError):
    def __init__(self, details: list[str]) -> None:
        super().__init__(
            code="MATCH_NOT_READY",
            message="Match configuration is incomplete.",
            status_code=409,
            details=details,
        )


class MatchNotReadyToStartError(AppError):
    def __init__(self, message: str = "Match is not ready to start.") -> None:
        super().__init__(code="MATCH_NOT_READY", message=message, status_code=409)


class MatchNotLiveError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="MATCH_NOT_LIVE",
            message="This match is not currently being scored.",
            status_code=409,
        )


class ScoreConflictError(ConflictError):
    def __init__(self, current_revision: int) -> None:
        super().__init__(
            "The score has changed. Refresh live state and retry.",
            code="SCORE_CONFLICT",
        )
        self.current_revision = current_revision


class NothingToUndoError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="NOTHING_TO_UNDO",
            message="There is no scoring action to undo.",
            status_code=409,
        )


class MatchNotCompletedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="MATCH_NOT_COMPLETED",
            message="This feature is only available for completed matches.",
            status_code=409,
        )


class ChatMessageTooLongError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="CHAT_MESSAGE_TOO_LONG",
            message="Keep questions under 1000 characters.",
            status_code=400,
        )


class AnalysisNotFoundError(ResourceNotFoundError):
    def __init__(self) -> None:
        super().__init__("Analysis not found.", code="ANALYSIS_NOT_FOUND")


class AIDisabledError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_DISABLED",
            message="AI analysis is currently disabled.",
            status_code=503,
        )


class AIProviderError(AppError):
    def __init__(self, message: str = "Unable to generate analysis right now.") -> None:
        super().__init__(code="AI_PROVIDER_ERROR", message=message, status_code=502)


class AITimeoutError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_TIMEOUT",
            message="The analysis request timed out.",
            status_code=504,
        )


class AIInvalidResponseError(AppError):
    def __init__(self, message: str = "The analysis response was invalid.") -> None:
        super().__init__(code="AI_INVALID_RESPONSE", message=message, status_code=502)


class AIGroundingFailedError(AppError):
    def __init__(self, message: str = "The analysis could not be grounded in match facts.") -> None:
        super().__init__(code="AI_GROUNDING_FAILED", message=message, status_code=502)


def _error_body(code: str, message: str, details: list[str] | None = None) -> dict[str, dict[str, object]]:
    error: dict[str, object] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        body = _error_body(exc.code, exc.message, exc.details)
        if isinstance(exc, ScoreConflictError):
            body["error"]["current_revision"] = exc.current_revision
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Request validation failed."),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", message),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )
