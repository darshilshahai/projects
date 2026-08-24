from __future__ import annotations

from fastapi import HTTPException, status


def raise_supabase_error(exc: Exception) -> None:
    """Map common PostgREST errors to clear HTTP responses."""
    message = str(exc)
    code = None
    if hasattr(exc, "code"):
        code = getattr(exc, "code")
    elif hasattr(exc, "args") and exc.args and isinstance(exc.args[0], dict):
        code = exc.args[0].get("code")
        message = exc.args[0].get("message") or message

    if code == "PGRST205" or "Could not find the table" in message:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database tables are missing. In the Supabase dashboard open "
                "SQL Editor, paste and run backend/sql/001_schema.sql, then retry."
            ),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    ) from exc
