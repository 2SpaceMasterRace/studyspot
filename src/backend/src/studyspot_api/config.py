"""Application configuration.

StudySpot has exactly two database variables, as documented in
``docs/source/database.md``. Neither value is ever exposed to browser code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "file:.local/studyspot.db"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings resolved from the process environment."""

    turso_database_url: str = DEFAULT_DATABASE_URL
    turso_auth_token: str | None = None

    @classmethod
    def from_environment(cls, environment: dict[str, str] | None = None) -> Settings:
        """Read settings from ``environment``, defaulting to the local embedded database."""
        source = os.environ if environment is None else environment
        url = (source.get("TURSO_DATABASE_URL") or "").strip() or DEFAULT_DATABASE_URL
        token = (source.get("TURSO_AUTH_TOKEN") or "").strip() or None
        return cls(turso_database_url=url, turso_auth_token=token)
