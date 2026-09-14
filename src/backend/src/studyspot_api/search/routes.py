"""Study-spot search HTTP endpoint."""

import os
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..spots.model import StudySpotSummary
from .client import MeilisearchClient, MeilisearchError

router = APIRouter(prefix="/spots", tags=["spots"])


async def get_search_client() -> AsyncIterator[MeilisearchClient]:
    yield MeilisearchClient(
        os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
        os.getenv("MEILISEARCH_API_KEY", ""),
        os.getenv("MEILISEARCH_INDEX", "spots"),
    )


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
