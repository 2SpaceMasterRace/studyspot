"""Root URL configuration.

These are the API's own paths. Publicly they all sit under ``/api``: CloudFront
and the Vercel rewrite both strip that prefix before the request arrives, so
``/api/health/live`` reaches ``health/live`` here. Nothing in Django needs to
know about the prefix, which is what keeps the two edges interchangeable.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .health import liveness

urlpatterns = [
    path("health/live", liveness, name="liveness"),
    path("", include("spots.urls")),
]

if settings.ENABLE_ADMIN:
    urlpatterns.append(path("admin/", admin.site.urls))
