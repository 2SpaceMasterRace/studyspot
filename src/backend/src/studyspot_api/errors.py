"""Structured error responses shared by every route.

Every non-2xx response has the same body:

.. code-block:: json

    {
      "error": {
        "code": "validation_error",
        "message": "The request could not be validated.",
        "details": [{"field": "query.limit", "message": "...", "type": "..."}]
      }
    }
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .spots.database import DatabaseUnavailable

logger = logging.getLogger(__name__)

STATUS_CODES = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
    422: "validation_error",
    500: "internal_error",
    503: "service_unavailable",
}


class ErrorDetail(BaseModel):
    """One specific problem with the request."""

    field: str | None = Field(default=None, description="Dotted path to the offending input.")
    message: str = Field(description="What is wrong with that input.")
    type: str | None = Field(default=None, description="Machine-readable failure kind.")


class ErrorBody(BaseModel):
    code: str = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Human-readable summary.")
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """The response body returned for every error."""

    error: ErrorBody


class ApiError(Exception):
    """An error that already knows how it should be reported."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


class NotFoundError(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(404, "not_found", message)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Render the shared error envelope."""
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def _field_path(location: tuple[Any, ...]) -> str | None:
    """Render a Pydantic error location as a dotted path."""
    parts = [str(part) for part in location]
    return ".".join(parts) if parts else None


def register_error_handlers(application: FastAPI) -> None:
    """Install the handlers that give every error the shared shape."""

    @application.exception_handler(ApiError)
    async def handle_api_error(_: Request, exception: ApiError) -> JSONResponse:
        return error_response(
            exception.status_code, exception.code, exception.message, exception.details
        )

    @application.exception_handler(DatabaseUnavailable)
    async def handle_database_unavailable(
        request: Request, exception: DatabaseUnavailable
    ) -> JSONResponse:
        logger.warning("Database unavailable for %s %s", request.method, request.url.path)
        return error_response(
            503, "database_unavailable", "The study-spot database is unavailable."
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request, exception: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=_field_path(error["loc"]),
                message=error["msg"],
                type=error["type"],
            )
            for error in exception.errors()
        ]
        return error_response(
            422, "validation_error", "The request could not be validated.", details
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(_: Request, exception: StarletteHTTPException) -> JSONResponse:
        code = STATUS_CODES.get(exception.status_code, "error")
        message = exception.detail if isinstance(exception.detail, str) else code
        return error_response(exception.status_code, code, message)

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception("Unhandled error for %s %s", request.method, request.url.path)
        return error_response(500, "internal_error", "The request could not be completed.")
