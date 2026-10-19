"""WSGI entry point, for a conventional application server."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyspot.settings")

application = get_wsgi_application()
