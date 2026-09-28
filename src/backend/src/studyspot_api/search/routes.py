"""Study-spot search HTTP endpoint."""

import json
import math
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from ..spots.hours import HoursStatus, hours_status_at
from ..spots.model import StudySpotSummary
from ..spots.repository import StudySpotRepository
from .client import MeilisearchClient, MeilisearchError

router = APIRouter(prefix="/spots", tags=["spots"])


async def get_search_client() -> AsyncIterator[MeilisearchClient]:
    yield MeilisearchClient(
        os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
        os.getenv("MEILISEARCH_API_KEY", ""),
        os.getenv("MEILISEARCH_INDEX", "spots"),
    )


def get_hours_statuses() -> dict[str, HoursStatus]:
    """Load and evaluate hours in FastAPI's worker pool, owning the connection there."""
    with StudySpotRepository(
        os.environ["TURSO_DATABASE_URL"], os.getenv("TURSO_AUTH_TOKEN", "")
    ) as repository:
        known_hours = repository.hours()
        now = datetime.now(UTC)
        return {
            identifier: hours_status_at(hours, now, latitude, longitude)
            for identifier, (hours, latitude, longitude) in known_hours.items()
        }


class FilteredSearchRequest(BaseModel):
    q: str = Field(default="", max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_miles: float | None = Field(default=None, gt=0, le=25)
    open_now: bool = False

    @model_validator(mode="after")
    def valid_location(self) -> "FilteredSearchRequest":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be provided together")
        if self.radius_miles is not None and self.latitude is None:
            raise ValueError("Radius requires a location")
        if any(
            value is not None and not math.isfinite(value)
            for value in (self.latitude, self.longitude, self.radius_miles)
        ):
            raise ValueError("Location and radius must be finite")
        return self


class FilteredSearchHit(StudySpotSummary):
    distance_miles: float | None = None
    hours_status: HoursStatus = "unknown"


def _distance_miles(latitude: float, longitude: float, spot: StudySpotSummary) -> float:
    """Great-circle distance between the user and a spot."""
    lat_1, lat_2 = math.radians(latitude), math.radians(spot.latitude)
    delta_lat = lat_2 - lat_1
    delta_lon = math.radians(spot.longitude - longitude)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_1) * math.cos(lat_2) * math.sin(delta_lon / 2) ** 2
    )
    return 3958.7613 * 2 * math.asin(min(1, math.sqrt(haversine)))


@router.get("/search", response_model=list[StudySpotSummary])
async def search_spots(
    q: Annotated[str, Query(...)],
    client: Annotated[MeilisearchClient, Depends(get_search_client)],
) -> list[StudySpotSummary]:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query must not be blank")
    try:
        return await client.search(query, limit=20)
    except MeilisearchError as error:
        raise HTTPException(status_code=503, detail="Search service unavailable") from error


@router.post("/search", response_model=list[FilteredSearchHit])
async def search_spots_with_filters(
    request: FilteredSearchRequest,
    client: Annotated[MeilisearchClient, Depends(get_search_client)],
    hours_statuses: Annotated[dict[str, HoursStatus], Depends(get_hours_statuses)],
) -> list[FilteredSearchHit]:
    """Combine text, radius, and live hours before applying the result limit."""
    filters: list[str] = []

    if request.radius_miles is not None:
        radius_meters = round(request.radius_miles * 1609.344)
        filters.append(f"_geoRadius({request.latitude}, {request.longitude}, {radius_meters})")

    if request.open_now:
        open_ids = [identifier for identifier, status in hours_statuses.items() if status == "open"]
        if not open_ids:
            return []
        filters.append(f"id IN [{', '.join(json.dumps(identifier) for identifier in open_ids)}]")

    try:
        matches = await client.search(request.q.strip(), limit=20, filters=filters)
    except MeilisearchError as error:
        raise HTTPException(status_code=503, detail="Search service unavailable") from error

    results: list[FilteredSearchHit] = []
    for match in matches:
        results.append(
            FilteredSearchHit(
                **match.model_dump(),
                distance_miles=(
                    round(_distance_miles(request.latitude, request.longitude, match), 2)
                    if request.latitude is not None and request.longitude is not None
                    else None
                ),
                hours_status=hours_statuses.get(match.id, "unknown"),
            )
        )
    return results
