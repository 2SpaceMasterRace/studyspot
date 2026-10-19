"""Settings for the test suite.

``settings.py`` refuses to start without ``DJANGO_SECRET_KEY`` when debug is off.
That is right for a deployment and unhelpful for ``uv run pytest``, which would
fail on import before collecting anything.

Rather than soften that guard, this module supplies the two values and then
defers entirely to the real settings, so the suite exercises the same
configuration every other environment does.

A conftest.py cannot do this job: pytest-django sets Django up from the
``pytest_load_initial_conftests`` hook, which runs before any conftest module is
imported, so environment defaults set there arrive too late.

``setdefault`` means an explicit export still wins -- CI sets ``DATABASE_URL``
this way, and a developer can point the suite at another database without
editing anything.
"""

import os

os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "django-insecure-test-key-not-for-deployment")

from .settings import *  # noqa: E402, F403
