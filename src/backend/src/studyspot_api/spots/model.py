"""Shared study-spot summary contract."""

from pydantic import BaseModel, ConfigDict

from .hours import SpotOpeningHours


class StudySpotSummary(BaseModel):
    """The eight fields shared by Turso, Meilisearch, and the HTTP API."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    category: str
    address: str
    neighborhood: str
    borough: str
    latitude: float
    longitude: float


class StudySpotRecord(StudySpotSummary):
    """A normalized source record; hours may be unavailable."""

    opening_hours: SpotOpeningHours | None = None
