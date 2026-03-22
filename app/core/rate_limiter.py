from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/docs") or request.url.path.startswith("/api/v1/openapi"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, 60)

            if current > self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                )
        except RuntimeError:
            pass

        response = await call_next(request)
        return response


async def check_rate_limit(
    identifier: str,
    limit: int = 60,
    window_seconds: int = 60,
) -> bool:
    """
    Check if an identifier has exceeded rate limit.
    Returns True if allowed, False if rate limited.
    """
    key = f"rate_limit:{identifier}"

    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)

        return current <= limit
    except RuntimeError:
        return True
