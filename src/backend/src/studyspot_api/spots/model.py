"""Shared study-spot summary contract."""

from pydantic import BaseModel, ConfigDict


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
