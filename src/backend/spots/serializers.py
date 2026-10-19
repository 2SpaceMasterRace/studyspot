"""Request and response serializers for the study-spot routes.

These belong to the HTTP layer rather than to ``models.py``: paging and query
validation are the route's concern, while the model is what the API, the loader,
and the search projection all agree on.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import DEFAULT_LIMIT, MAX_FILTER_LENGTH, MAX_LIMIT, Borough, StudySpot


class StudySpotSerializer(serializers.ModelSerializer):
    """The shared study-spot summary.

    The field list is explicit rather than ``__all__``: this response shape is
    the shared contract, and a column added to the model should not silently
    become part of the public API.
    """

    class Meta:
        model = StudySpot
        fields = [
            "id",
            "name",
            "category",
            "address",
            "neighborhood",
            "borough",
            "latitude",
            "longitude",
            "university",
        ]


class BoroughField(serializers.CharField):
    """A borough name in any casing or internal spacing.

    ``?borough=brooklyn`` and ``?borough=  Staten   Island `` both resolve, which
    is the behaviour the published contract describes.
    """

    def to_internal_value(self, data: Any) -> str:
        value = super().to_internal_value(data)
        wanted = " ".join(value.split()).casefold()
        for borough in Borough.values:
            if borough.casefold() == wanted:
                return borough
        raise serializers.ValidationError(
            f"Must be one of the five boroughs: {', '.join(Borough.values)}."
        )


def filter_field(help_text: str) -> serializers.CharField:
    """A trimmed, non-blank, bounded filter value."""
    return serializers.CharField(
        required=False,
        trim_whitespace=True,
        min_length=1,
        max_length=MAX_FILTER_LENGTH,
        help_text=help_text,
    )


class SpotQuerySerializer(serializers.Serializer):
    """Query parameters for ``GET /spots``. Unknown parameters are rejected."""

    name = filter_field("Case-insensitive substring match on the spot name.")
    neighborhood = filter_field("Case-insensitive exact match on the neighborhood name.")
    borough = BoroughField(
        required=False,
        trim_whitespace=True,
        min_length=1,
        max_length=MAX_FILTER_LENGTH,
        help_text="Case-insensitive exact match on one of the five boroughs.",
    )
    university = filter_field(
        "Case-insensitive exact match on the institution a spot belongs to. Only "
        "records the importer takes from a curated campus list carry one, so "
        "every other spot is excluded when this filter is used."
    )

    limit = serializers.IntegerField(
        required=False,
        default=DEFAULT_LIMIT,
        min_value=1,
        max_value=MAX_LIMIT,
        help_text=f"Page size, 1 to {MAX_LIMIT}.",
    )
    offset = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Rows to skip before this page.",
    )

    def to_internal_value(self, data: Any) -> dict[str, Any]:
        """Reject parameters this endpoint does not define, and blank values.

        A misspelled filter that is silently ignored returns a plausible page of
        the wrong results, which is worse than an error. The previous
        implementation forbade extra fields for the same reason.
        """
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise serializers.ValidationError(
                {name: "Unknown query parameter." for name in unknown}
            )

        # ``?name=`` has to be rejected explicitly. A QueryDict is HTML input as
        # far as DRF is concerned, and for an optional field that does not allow
        # blanks, DRF reads an empty value as "not supplied" and drops it. The
        # published contract treats a present-but-empty parameter as a bad
        # request, and silently widening a search because its value was lost is
        # the same failure as ignoring a misspelled one.
        blank = sorted(
            name
            for name in self.fields
            if name in data and isinstance(data[name], str) and not data[name].strip()
        )
        if blank:
            raise serializers.ValidationError(
                {name: "This field may not be blank." for name in blank}
            )

        return super().to_internal_value(data)
