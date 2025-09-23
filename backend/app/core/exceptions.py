"""
Global exception handlers and custom exceptions.
Provides consistent error handling across the application.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentException(AppException):
    """Agent-related exceptions."""
    pass


class CallException(AppException):
    """Call-related exceptions."""
    pass


class RetellException(AppException):
    """Retell API exceptions."""
    pass


class AuthenticationException(AppException):
    """Authentication exceptions."""

    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationException(AppException):
    """Authorization exceptions."""

    def __init__(self, message: str = "Insufficient permissions", details: Dict[str, Any] = None):
        super().__init__(message, status_code=403, details=details)


class ResourceNotFoundException(AppException):
    """Resource not found exceptions."""

    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    """Validation exceptions."""

    def __init__(self, message: str, field_errors: Dict[str, str] = None):
        super().__init__(message, status_code=422, details={"field_errors": field_errors or {}})


class ConflictException(AppException):
    """Resource conflict exceptions."""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, status_code=409, details=details)


class RateLimitException(AppException):
    """Rate limiting exceptions."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(f"Application exception: {exc.message}", extra={
        "status_code": exc.status_code,
        "details": exc.details,
        "path": request.url.path,
        "method": request.method
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "HTTPException"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "path": request.url.path,
        "method": request.method
    })

    # Format validation errors for better UX
    field_errors = {}
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        field_errors[field_path] = error["msg"]

    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "details": {
                "field_errors": field_errors,
                "raw_errors": exc.errors()
            },
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected exception: {str(exc)}", extra={
        "exception_type": exc.__class__.__name__,
        "path": request.url.path,
        "method": request.method
    }, exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "type": "InternalServerError"
        }
    )


def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)