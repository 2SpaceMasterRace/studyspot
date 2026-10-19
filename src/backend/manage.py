#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyspot.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Is it installed and is the virtual "
            "environment active? Run `uv sync --frozen` in src/backend/."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
