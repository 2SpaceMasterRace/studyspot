"""Structured error responses shared by every route.

Every non-2xx response has the same body, which is part of the shared contract
in ``docs/source/api.md``:

.. code-block:: json

    {
      "error": {
        "code": "validation_error",
        "message": "The request could not be validated.",
        "details": [{"field": "query.limit", "message": "...", "type": "..."}]
      }
    }

Django REST Framework's own error bodies are shaped per exception type, so this
module normalizes them. Keeping the envelope identical to the one the previous
implementation produced is what lets the frontend and the published API guide
survive the move to Django unchanged.
"""

from __future__ import annotations

import logging
from typing import Any

from django.http import JsonResponse
from rest_framework import status as http_status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    422: "validation_error",
    500: "internal_error",
    503: "service_unavailable",
}


def envelope(
    code: str, message: str, details: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Render the shared error envelope as a plain dictionary."""
    return {"error": {"code": code, "message": message, "details": details or []}}


def error_json_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JsonResponse:
    """Render the envelope for code outside a DRF view, such as middleware."""
    return JsonResponse(envelope(code, message, details), status=status_code)


def flatten_details(detail: Any, prefix: str = "") -> list[dict[str, Any]]:
    """Flatten a DRF validation detail into the contract's ``details`` list.

    DRF nests these arbitrarily: a dict of field names to lists of messages, a
    bare list for non-field errors, or a single string. The contract wants one
    flat list of ``{field, message, type}``, with a dotted path for the field.
    """
    if isinstance(detail, dict):
        found: list[dict[str, Any]] = []
        for key, value in detail.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            found.extend(flatten_details(value, child))
        return found

    if isinstance(detail, list):
        found = []
        for item in detail:
            found.extend(flatten_details(item, prefix))
        return found

    return [
        {
            "field": prefix or None,
            "message": str(detail),
            # DRF attaches a machine-readable code to each message via the
            # ErrorDetail str subclass.
            "type": getattr(detail, "code", None),
        }
    ]


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Give every DRF exception the shared envelope.

    Returning ``None`` hands the exception back to Django, which is what should
    happen for anything that is not an API error.
    """
    if isinstance(exc, ValidationError):
        # 422 rather than DRF's 400: the published contract says a request that
        # fails validation is Unprocessable Content, and the frontend
        # distinguishes it from a malformed request.
        return Response(
            envelope(
                "validation_error",
                "The request could not be validated.",
                flatten_details(exc.detail, prefix="query"),
            ),
            status=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    code = STATUS_CODES.get(status_code, "error")
    message = "The request could not be completed."

    if isinstance(exc, APIException):
        detail = exc.detail
        if isinstance(detail, str):
            message = str(detail)

    response.data = envelope(code, message)
    return response
