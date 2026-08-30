from typing import Any, Dict, Optional
from fastapi import status


class AppException(Exception):
    """Base application domain exception."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class EmailAlreadyExistsException(AppException):
    def __init__(self, message: str = "User with this email already exists."):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidTokenException(AppException):
    def __init__(self, message: str = "Invalid or expired token."):
        super().__init__(
            code="INVALID_TOKEN",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class RevokedTokenException(AppException):
    def __init__(self, message: str = "Refresh token has been revoked."):
        super().__init__(
            code="TOKEN_REVOKED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InactiveUserException(AppException):
    def __init__(self, message: str = "User account is inactive."):
        super().__init__(
            code="INACTIVE_USER",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access denied."):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class DuplicateResourceException(AppException):
    def __init__(self, message: str = "Video already exists in your library."):
        super().__init__(
            code="DUPLICATE_RESOURCE",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


# YouTube Integration Exceptions
class InvalidYouTubeURLException(AppException):
    def __init__(self, message: str = "Invalid YouTube URL format."):
        super().__init__(
            code="INVALID_YOUTUBE_URL",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class YouTubeVideoNotFoundException(AppException):
    def __init__(self, message: str = "YouTube video not found or is private/deleted."):
        super().__init__(
            code="YOUTUBE_VIDEO_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class YouTubeAPIQuotaExceededException(AppException):
    def __init__(self, message: str = "YouTube API quota limit reached. Using metadata fallback."):
        super().__init__(
            code="YOUTUBE_QUOTA_EXCEEDED",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class YouTubeServiceException(AppException):
    def __init__(self, message: str = "Failed to communicate with YouTube API."):
        super().__init__(
            code="YOUTUBE_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
