class ApplicationError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "application_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class DatasetNotFoundError(ApplicationError):
    def __init__(self, dataset_id: str) -> None:
        super().__init__(
            f"Dataset '{dataset_id}' was not found.",
            status_code=404,
            error_code="dataset_not_found",
        )


class UnsupportedFileTypeError(ApplicationError):
    def __init__(self, filename: str) -> None:
        super().__init__(
            f"Unsupported file type for '{filename}'. Only CSV files are allowed.",
            status_code=415,
            error_code="unsupported_file_type",
        )


class EmptyFileError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "The uploaded file is empty.",
            status_code=400,
            error_code="empty_file",
        )


class FileTooLargeError(ApplicationError):
    def __init__(self, maximum_size_mb: int) -> None:
        super().__init__(
            f"The uploaded file exceeds the {maximum_size_mb} MB limit.",
            status_code=413,
            error_code="file_too_large",
        )


class InvalidCSVError(ApplicationError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            f"The uploaded file could not be parsed as CSV: {reason}",
            status_code=422,
            error_code="invalid_csv",
        )

class OpenAIConfigurationError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "OPENAI_API_KEY is not configured.",
            status_code=500,
            error_code="openai_not_configured",
        )


class AIAnalysisError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            status_code=502,
            error_code="ai_analysis_error",
        )


class SQLValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            status_code=400,
            error_code="sql_validation_error",
        )


class SQLExecutionError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            status_code=422,
            error_code="sql_execution_error",
        )

class ChartValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            status_code=422,
            error_code="chart_validation_error",
        )