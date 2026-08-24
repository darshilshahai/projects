import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter suitable for single-instance/demo deployments."""

    def __init__(self, app, limit: int = 5, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path.endswith("/analyze"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            hits = self._hits[client_ip]

            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()

            if len(hits) >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many analyses. Please wait a moment and try again."
                    },
                )

            hits.append(now)

        return await call_next(request)
