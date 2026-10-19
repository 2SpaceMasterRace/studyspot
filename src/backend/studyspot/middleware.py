"""Cross-cutting request handling.

Django REST Framework's exception handler only sees exceptions that subclass
``APIException``, so a database that cannot answer would otherwise reach the
client as a bare 500 with a stack trace. The contract says it is a 503 with the
``database_unavailable`` code, which is what this restores.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from django.db import InterfaceError, OperationalError, ProgrammingError
from django.http import HttpRequest, HttpResponse, JsonResponse

from .errors import error_json_response

logger = logging.getLogger(__name__)

#: ``OperationalError`` covers a refused connection, a resolution failure, and a
#: statement timeout. ``InterfaceError`` covers a connection that was already
#: closed. ``ProgrammingError`` covers the missing table a database that has
#: never been migrated produces.
#:
#: Deliberately not ``DatabaseError``: ``IntegrityError`` descends from it, and a
#: constraint violation on a future write path is the caller's mistake rather
#: than an outage.
UNAVAILABLE = (OperationalError, InterfaceError, ProgrammingError)


class DatabaseUnavailableMiddleware:
    """Report an unreachable or unmigrated database as a 503."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> JsonResponse | None:
        if not isinstance(exception, UNAVAILABLE):
            return None

        # Logged rather than returned: the driver's message names the host, the
        # database, and sometimes the failing statement.
        logger.warning(
            "Database unavailable for %s %s: %s",
            request.method,
            request.path,
            exception,
        )
        return error_json_response(
            503,
            "database_unavailable",
            "The study-spot database is unavailable.",
        )
