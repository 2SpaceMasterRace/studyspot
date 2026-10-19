"""ASGI entry point.

Used by the Lambda handler through Mangum, and by the Vercel entry point in
``main.py``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyspot.settings")

application = get_asgi_application()
