"""Connections to the Turso serving database.

One interface covers both deployments, as ``docs/source/database.md`` requires:

- a local ``file:`` URL is a filesystem path handed to :func:`turso.connect`; and
- a hosted URL plus token is handed to :func:`libsql.connect`.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

LOCAL_URL_PREFIX = "file:"
IN_MEMORY = ":memory:"


class Connection(Protocol):
    """The subset of the DB-API surface both Turso drivers provide."""

    def cursor(self) -> Any: ...

    def commit(self) -> None: ...

    def close(self) -> None: ...


class DatabaseUnavailable(RuntimeError):
    """The database could not answer.

    The HTTP layer maps this to a 503; command-line callers let it surface.
    """


def local_database_path(url: str) -> Path:
    """Interpret a local ``file:`` URL as a filesystem path."""
    remainder = url[len(LOCAL_URL_PREFIX) :]
    if remainder.startswith("//"):
        remainder = remainder[2:]
    return Path(remainder or IN_MEMORY)


class Database:
    """Opens connections to whichever Turso database is configured."""

    def __init__(self, url: str, auth_token: str | None = None) -> None:
        self.url = url
        self.auth_token = auth_token

    @property
    def is_local(self) -> bool:
        """True when the database is an embedded file rather than Turso Cloud."""
        return self.url.startswith(LOCAL_URL_PREFIX)

    @property
    def driver(self) -> ModuleType:
        """The driver module for this database.

        Imported lazily so a local deployment never needs the remote driver installed.
        """
        if self.is_local:
            import turso

            return turso
        import libsql

        return libsql

    @property
    def errors(self) -> tuple[type[BaseException], ...]:
        """Driver exceptions that mean the database could not answer."""
        return (self.driver.Error,)

    def connect(self) -> Connection:
        """Open a new connection. Callers own it and must close it."""
        if not self.is_local:
            if not self.auth_token:
                raise DatabaseUnavailable(
                    f"TURSO_AUTH_TOKEN is required for the remote database {self.url!r}"
                )
            return self.driver.connect(self.url, auth_token=self.auth_token)
        path = local_database_path(self.url)
        if str(path) != IN_MEMORY and path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        return self.driver.connect(str(path))
