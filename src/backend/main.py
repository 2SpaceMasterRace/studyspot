"""Vercel entry point for the StudySpot API service.

Vercel's Python runtime looks for an ASGI or WSGI callable named by
``vercel.json``'s ``entrypoint``. The AWS entry point is ``handler.py`` beside
this file; both import the same application.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyspot.settings")

from studyspot.asgi import application  # noqa: E402

#: Vercel's configured entrypoint is ``main:app``.
app = application

__all__ = ["app", "application"]
