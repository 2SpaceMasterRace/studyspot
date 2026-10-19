"""Public study-spot routes."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudySpot
from .serializers import SpotQuerySerializer, StudySpotSerializer

#: Maps a validated query parameter to the lookup it filters with. Substring for
#: the name, exact for the rest, all case-insensitive. A `university` or
#: `neighborhood` filter therefore excludes rows where the column is NULL, which
#: is the documented behaviour.
LOOKUPS = {
    "name": "name__icontains",
    "neighborhood": "neighborhood__iexact",
    "borough": "borough__iexact",
    "university": "university__iexact",
}


def apply_filters(queryset: QuerySet[StudySpot], parameters: dict[str, Any]) -> QuerySet[StudySpot]:
    """Narrow ``queryset`` by every filter the caller supplied.

    Django escapes the LIKE wildcards in an ``icontains`` value, so a search for
    ``100%`` is a search for a literal percent sign.
    """
    lookups = {
        lookup: parameters[parameter]
        for parameter, lookup in LOOKUPS.items()
        if parameters.get(parameter) is not None
    }
    return queryset.filter(**lookups) if lookups else queryset


class SpotListView(APIView):
    """``GET /spots`` -- a filtered, paginated page of study spots."""

    def get(self, request: Request) -> Response:
        query = SpotQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        parameters = query.validated_data

        limit: int = parameters["limit"]
        offset: int = parameters["offset"]

        matching = apply_filters(StudySpot.objects.all(), parameters)

        # Counted before slicing, because the envelope reports the size of the
        # whole result set rather than of this page.
        total = matching.count()
        items = StudySpotSerializer(matching[offset : offset + limit], many=True).data

        return Response(
            {
                "items": items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(items),
                    "total": total,
                    "has_more": offset + len(items) < total,
                },
            }
        )


class SpotDetailView(APIView):
    """``GET /spots/{id}`` -- one study spot."""

    def get(self, request: Request, spot_id: str) -> Response:
        try:
            spot = StudySpot.objects.get(pk=spot_id)
        except StudySpot.DoesNotExist:
            raise NotFound(f"No study spot has the identifier {spot_id!r}.") from None
        return Response(StudySpotSerializer(spot).data)
