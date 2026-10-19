"""Study-spot routes.

No trailing slashes, and ``APPEND_SLASH`` is off in settings, because the
published contract is ``/spots`` and ``/spots/{id}``.

A spot identifier carries its source dataset as a prefix, as in
``facdb:eec118768e15a5e03d3354abda7b00da``. ``str`` matches that colon; it
matches anything except a slash.
"""

from django.urls import path

from .views import SpotDetailView, SpotListView

urlpatterns = [
    path("spots", SpotListView.as_view(), name="spot-list"),
    path("spots/<str:spot_id>", SpotDetailView.as_view(), name="spot-detail"),
]
