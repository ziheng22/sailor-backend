import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..config import settings

AUTH_PATHS = frozenset({
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/initialize-password",
})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.public_base_url.startswith("https://"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_per_minute: int = 30):
        super().__init__(app)
        self.max_per_minute = max_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "POST" and request.url.path in AUTH_PATHS:
            client = request.client.host if request.client else "unknown"
            now = time.time()
            window = self._hits[client]
            window[:] = [t for t in window if now - t < 60]
            if len(window) >= self.max_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                )
            window.append(now)
        return await call_next(request)
