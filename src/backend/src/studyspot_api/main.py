"""StudySpot API application composition."""

from fastapi import FastAPI

from .health import router as health_router
from .search.routes import router as search_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="StudySpot API")
    application.include_router(health_router)
    application.include_router(search_router)
    return application


app = create_app()
