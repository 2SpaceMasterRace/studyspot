"""Process health endpoints."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Response returned when the API process is alive."""

    status: Literal["ok"]


@router.get("/live", response_model=HealthResponse)
async def get_liveness() -> HealthResponse:
    """Report that the API process can serve requests."""
    return HealthResponse(status="ok")
