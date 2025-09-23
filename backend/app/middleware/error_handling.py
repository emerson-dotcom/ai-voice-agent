"""
Error handling middleware for request/response processing.
Provides consistent error logging and response formatting.
"""

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors and add request tracking."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request ID to headers
        start_time = time.time()

        # Log incoming request
        logger.info(f"Request started", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        })

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful response
            logger.info(f"Request completed", extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 3)
            })

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 3))

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log error
            logger.error(f"Request failed", extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "process_time": round(process_time, 3)
            }, exc_info=True)

            # Re-raise to let exception handlers deal with it
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CORS headers for development (should be configured properly in production)
        if request.headers.get("origin"):
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin")
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_requests = {}  # In production, use Redis or similar

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time() / 60)  # Current minute

        # Clean old entries
        self.client_requests = {
            ip: times for ip, times in self.client_requests.items()
            if any(t >= current_time - 1 for t in times)
        }

        # Check rate limit
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []

        # Count requests in current and previous minute
        recent_requests = [
            t for t in self.client_requests[client_ip]
            if t >= current_time - 1
        ]

        if len(recent_requests) >= self.calls_per_minute:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # Record this request
        self.client_requests[client_ip].append(current_time)

        return await call_next(request)