"""Turso/libSQL connection adapter.

StudySpot serves from a single libSQL database that is either a local embedded
file (local development and Docker Compose) or a Turso Cloud database (Vercel
Preview and Production). Both are reached through one interface here so callers
never branch on the environment.

Configuration comes from two variables, matching the deployment model in
``docs/source/database.md``::

    TURSO_DATABASE_URL   # file:.local/studyspot.db  or  libsql://<db>.turso.io
    TURSO_AUTH_TOKEN     # empty for a local file, required for Turso Cloud

Never expose either value to browser code; the API owns all database access.
"""

from __future__ import annotations

import os

import libsql

TURSO_DATABASE_URL_ENV = "TURSO_DATABASE_URL"
TURSO_AUTH_TOKEN_ENV = "TURSO_AUTH_TOKEN"


def _resolve_local_path(database_url: str) -> str | None:
    """Return a filesystem path for a local ``file:`` URL, else ``None``.

    A local libSQL database is addressed as ``file:<path>``. Everything else
    (``libsql://``, ``https://``, ``wss://``) is a remote Turso Cloud endpoint.
    """
    if database_url.startswith("file:"):
        return database_url[len("file:") :]
    return None


def connect(
    database_url: str | None = None,
    auth_token: str | None = None,
) -> libsql.Connection:  # ty: ignore[unresolved-attribute]  # libsql ships no type stubs
    """Connect to the configured libSQL database.

    ``database_url`` and ``auth_token`` default to the ``TURSO_DATABASE_URL`` and
    ``TURSO_AUTH_TOKEN`` environment variables. A ``file:`` URL opens a local
    embedded database and ignores the token; any other URL connects to Turso
    Cloud and requires the token.
    """
    database_url = (
        database_url if database_url is not None else os.environ.get(TURSO_DATABASE_URL_ENV)
    )
    if not database_url:
        raise RuntimeError(
            f"{TURSO_DATABASE_URL_ENV} is not set; expected a file: path or a Turso Cloud URL"
        )

    auth_token = auth_token if auth_token is not None else os.environ.get(TURSO_AUTH_TOKEN_ENV, "")

    local_path = _resolve_local_path(database_url)
    if local_path is not None:
        return libsql.connect(local_path)  # ty: ignore[unresolved-attribute]

    if not auth_token:
        raise RuntimeError(
            f"{TURSO_AUTH_TOKEN_ENV} is required for the remote database {database_url!r}"
        )
    return libsql.connect(database_url, auth_token=auth_token)  # ty: ignore[unresolved-attribute]
