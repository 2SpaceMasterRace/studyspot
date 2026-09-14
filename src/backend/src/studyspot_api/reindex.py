"""Rebuild the Meilisearch projection from Turso."""

import asyncio
import os

from .search.client import MeilisearchClient
from .spots.repository import StudySpotRepository


async def reindex() -> int:
    with StudySpotRepository(
        os.environ["TURSO_DATABASE_URL"], os.getenv("TURSO_AUTH_TOKEN", "")
    ) as repository:
        spots = repository.all()
    client = MeilisearchClient(
        os.environ["MEILISEARCH_URL"],
        os.getenv("MEILISEARCH_API_KEY", ""),
        os.getenv("MEILISEARCH_INDEX", "spots"),
    )
    await client.configure()
    return await client.replace_documents(spots)


if __name__ == "__main__":
    print(f"Indexed {asyncio.run(reindex())} study spots")
