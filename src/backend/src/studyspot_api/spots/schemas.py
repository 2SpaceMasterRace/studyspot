"""Request and response models for the study-spot routes.

These belong to the HTTP layer rather than to `models.py`: paging and query
validation are the route's concern, while the shared contract is what the API, the
search projection, and the loader all agree on.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .models import DEFAULT_LIMIT, MAX_LIMIT, Borough, FilterText, StudySpot


class SpotQuery(BaseModel):
    """Query parameters for ``GET /spots``. Unknown parameters are rejected."""

    model_config = ConfigDict(extra="forbid")

    name: FilterText | None = Field(
        default=None, description="Case-insensitive substring match on the spot name."
    )
    neighborhood: FilterText | None = Field(
        default=None, description="Case-insensitive exact match on the neighborhood name."
    )
    borough: Borough | None = Field(
        default=None, description="Case-insensitive exact match on one of the five boroughs."
    )
    university: FilterText | None = Field(
        default=None,
        description="Case-insensitive exact match on the institution a spot belongs to. "
        "Only records the importer takes from a curated campus list carry one, so every "
        "other spot is excluded when this filter is used.",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description=f"Page size, 1 to {MAX_LIMIT}."
    )
    offset: int = Field(default=0, ge=0, description="Rows to skip before this page.")


class Pagination(BaseModel):
    """Where this page sits in the full result set."""

    limit: int
    offset: int
    count: int
    total: int
    has_more: bool


class SpotPage(BaseModel):
    """A page of study spots."""

    items: list[StudySpot]
    pagination: Pagination
