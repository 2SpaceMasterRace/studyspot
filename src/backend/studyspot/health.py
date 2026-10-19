"""Process health endpoints."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def liveness(request: HttpRequest) -> JsonResponse:
    """Report that the API process can serve requests.

    This deliberately does not touch Postgres. It answers whether the process is
    alive, and a check that fails because a dependency is down cannot tell you
    which of the two to restart. Readiness, which does contact the database, is
    a separate endpoint owned by a later milestone.
    """
    return JsonResponse({"status": "ok"})
