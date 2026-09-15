"""Public study-spot routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from ..errors import ErrorResponse, NotFoundError
from .models import SpotFilters, StudySpot
from .repository import SpotRepository
from .schemas import Pagination, SpotPage, SpotQuery

router = APIRouter(prefix="/spots", tags=["spots"])

ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    422: {"model": ErrorResponse, "description": "The request could not be validated."},
    503: {"model": ErrorResponse, "description": "The study-spot database is unavailable."},
}

NOT_FOUND_RESPONSE: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorResponse, "description": "No spot has that identifier."},
    **ERROR_RESPONSES,
}


def get_repository(request: Request) -> SpotRepository:
    """Resolve the repository the application was composed with."""
    return request.app.state.spot_repository


Repository = Annotated[SpotRepository, Depends(get_repository)]


@router.get(
    "",
    response_model=SpotPage,
    summary="List study spots",
    responses=ERROR_RESPONSES,
)
def list_spots(query: Annotated[SpotQuery, Query()], repository: Repository) -> SpotPage:
    """Return a page of study spots matching every filter supplied.

    Results are ordered by name then identifier, so paging over an unchanged dataset
    never repeats or skips a spot.
    """
    filters = SpotFilters(
        name=query.name,
        neighborhood=query.neighborhood,
        borough=query.borough.value if query.borough else None,
        university=query.university,
    )
    items, total = repository.list_spots(filters, limit=query.limit, offset=query.offset)
    return SpotPage(
        items=items,
        pagination=Pagination(
            limit=query.limit,
            offset=query.offset,
            count=len(items),
            total=total,
            has_more=query.offset + len(items) < total,
        ),
    )


@router.get(
    "/{spot_id}",
    response_model=StudySpot,
    summary="Get one study spot",
    responses=NOT_FOUND_RESPONSE,
)
def get_spot(spot_id: str, repository: Repository) -> StudySpot:
    """Return a single study spot by identifier."""
    spot = repository.get_spot(spot_id)
    if spot is None:
        raise NotFoundError(f"No study spot has the identifier {spot_id!r}.")
    return spot
