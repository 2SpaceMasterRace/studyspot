"""Admin registration for study spots.

Registering is harmless when ``DJANGO_ENABLE_ADMIN`` is off, because
``studyspot/urls.py`` then never mounts the admin URLs at all.

The dataset is a rebuildable projection of ``data/spots.json``, so edits made
here are overwritten by the next ``load_spots`` run. The admin is for looking,
which is why everything below is read-only.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from .models import StudySpot


@admin.register(StudySpot)
class StudySpotAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "neighborhood", "borough", "university")
    list_filter = ("borough", "category")
    search_fields = ("name", "neighborhood", "university", "address")
    ordering = ("name", "id")
    readonly_fields = tuple(field.name for field in StudySpot._meta.fields)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
