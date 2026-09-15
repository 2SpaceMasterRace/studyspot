"""The shared study-spot contract.

One model serves the HTTP API, the search projection, and the dataset loader, so
those three cannot drift apart.

Nullability follows what NYC Open Data actually supplies rather than what would be
convenient. In the committed snapshots, ``address`` and ``neighborhood`` are both
genuinely absent for some records, so requiring them would reject real rows.
``university`` is absent for every record the importer does not take from a curated
campus list, which is most of them, and a snapshot produced before the field existed
still validates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

#: Filter values are trimmed, must not be blank, and are bounded.
FilterText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]


class Borough(StrEnum):
    """The five New York City boroughs. Accepts any casing of its value."""

    MANHATTAN = "Manhattan"
    BROOKLYN = "Brooklyn"
    QUEENS = "Queens"
    BRONX = "Bronx"
    STATEN_ISLAND = "Staten Island"

    @classmethod
    def _missing_(cls, value: object) -> Borough | None:
        if isinstance(value, str):
            wanted = " ".join(value.split()).casefold()
            for member in cls:
                if member.value.casefold() == wanted:
                    return member
        return None


class StudySpot(BaseModel):
    """One study spot.

    ``category`` is a free string rather than an enumeration: the vocabulary belongs
    to the data importer, and pinning it here would force every category change
    through the shared contract.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Stable identifier, prefixed with its source dataset.")
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    address: str | None = None
    neighborhood: str | None = Field(
        default=None, description="Neighborhood name, when the source supplies one."
    )
    borough: Borough
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    university: str | None = Field(
        default=None,
        description="The institution this spot belongs to, for records the importer takes "
        "from a curated campus list. Never inferred: a spot with no curated affiliation "
        "leaves this absent.",
    )


@dataclass(frozen=True, slots=True)
class SpotFilters:
    """The filters a caller may combine. Every one is case-insensitive."""

    name: str | None = None
    neighborhood: str | None = None
    borough: str | None = None
    university: str | None = None
