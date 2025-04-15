"""
Structured JSON logging middleware with performance timing.

Logs every request with:
- method, path, status_code
- preprocessing_ms, inference_ms, total_ms (when set by inference service)
- user_id (from JWT if available)
- request_id (UUID for tracing)
"""

import time
import uuid
import logging
import json
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every request in structured JSON format.

    Also injects timing information into the request state so that
    downstream handlers can record preprocessing_ms, inference_ms, etc.
    """

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("truthlens.api")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.timing = {}  # Downstream can set: timing["preprocessing_ms"], etc.

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            total_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._log_request(request, 500, total_ms, request_id, error=str(exc))
            raise

        total_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self._log_request(request, response.status_code, total_ms, request_id)

        # Add request ID to response headers for client-side tracing
        response.headers["X-Request-ID"] = request_id
        return response

    def _log_request(
        self,
        request: Request,
        status_code: int,
        total_ms: float,
        request_id: str,
        error: str | None = None,
    ):
        """Emit a structured JSON log entry."""
        # Extract user ID from JWT if available
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.auth.service import decode_access_token
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                user_id = payload.get("sub")
            except Exception:
                pass

        # Build log entry
        log_entry = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "status_code": status_code,
            "user_id": user_id,
            "client_ip": request.client.host if request.client else None,
            "total_ms": total_ms,
        }

        # Add timing breakdown if set by downstream handlers
        timing = getattr(request.state, "timing", {})
        if timing:
            log_entry.update({
                "preprocessing_ms": timing.get("preprocessing_ms"),
                "inference_ms": timing.get("inference_ms"),
                "explainability_ms": timing.get("explainability_ms"),
            })

        if error:
            log_entry["error"] = error
            self.logger.error(json.dumps(log_entry))
        elif status_code >= 400:
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry))
