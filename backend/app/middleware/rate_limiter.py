"""
Rate limiting middleware using SlowAPI.
Enforces 60 requests/minute per user (by IP for unauthenticated, by user ID for authenticated).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.config import settings


def _get_rate_limit_key(request: Request) -> str:
    """
    Rate limit key function.
    Uses user ID from JWT if available, falls back to IP address.
    """
    # Try to extract user from authorization header (lightweight check)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.auth.service import decode_access_token
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            return payload.get("sub", get_remote_address(request))
        except Exception:
            pass
    return get_remote_address(request)


# Limiter instance
limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": str(exc.detail).split("per")[0].strip() if exc.detail else "60 seconds",
        },
    )
