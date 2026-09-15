"""StudySpot API application composition."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings
from .errors import register_error_handlers
from .health import router as health_router
from .spots.database import Database
from .spots.repository import TursoSpotRepository
from .spots.router import router as spots_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Compose the study-spot repository around the configured Turso database."""
    settings = Settings.from_environment()
    database = Database(settings.turso_database_url, settings.turso_auth_token)
    application.state.spot_repository = TursoSpotRepository(database)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="StudySpot API", lifespan=lifespan)
    register_error_handlers(application)
    application.include_router(health_router)
    application.include_router(spots_router)
    return application


app = create_app()
