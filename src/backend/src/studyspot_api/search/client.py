"""Async REST client for the Meilisearch projection."""

import asyncio
from collections.abc import Iterable
from typing import Any

import httpx

from ..spots.model import StudySpotSummary

SEARCHABLE_ATTRIBUTES = ["name", "neighborhood", "category", "address", "borough"]
INDEX_SETTINGS: dict[str, Any] = {
    "searchableAttributes": SEARCHABLE_ATTRIBUTES,
    "prefixSearch": "indexingTime",
    "typoTolerance": {
        "enabled": True,
        "minWordSizeForTypos": {"oneTypo": 5, "twoTypos": 9},
        "disableOnWords": [],
        "disableOnAttributes": [],
        "disableOnNumbers": False,
    },
}
TERMINAL_FAILURES = {"failed", "canceled"}


class MeilisearchError(RuntimeError):
    """Raised when Meilisearch cannot fulfill an operation."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MeilisearchClient:
    """Minimal async client with explicit request and task timeouts."""

    def __init__(
        self,
        url: str,
        api_key: str = "",
        index: str = "spots",
        timeout: float = 5,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.index = index
        self.timeout = timeout
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self._headers(), **kwargs.pop("headers", {})}
        try:
            async with httpx.AsyncClient(
                base_url=self.url, timeout=self.timeout, transport=self.transport
            ) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            status_code = (
                error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
            )
            raise MeilisearchError("Meilisearch request failed", status_code) from error

    async def search(self, query: str, limit: int = 20) -> list[StudySpotSummary]:
        payload = await self._request(
            "POST", f"/indexes/{self.index}/search", json={"q": query, "limit": limit}
        )
        return [StudySpotSummary(**hit) for hit in payload.get("hits", [])]

    async def configure(self) -> None:
        try:
            await self._request("GET", f"/indexes/{self.index}")
        except MeilisearchError as error:
            if error.status_code != 404:
                raise
            task = await self._request(
                "POST", "/indexes", json={"uid": self.index, "primaryKey": "id"}
            )
            await self.wait_for_task(task["taskUid"])
        task = await self._request("PATCH", f"/indexes/{self.index}/settings", json=INDEX_SETTINGS)
        await self.wait_for_task(task["taskUid"])

    async def replace_documents(self, documents: Iterable[StudySpotSummary]) -> int:
        delete = await self._request("DELETE", f"/indexes/{self.index}/documents")
        await self.wait_for_task(delete["taskUid"])
        payload = [document.model_dump() for document in documents]
        if not payload:
            return 0
        task = await self._request("POST", f"/indexes/{self.index}/documents", json=payload)
        await self.wait_for_task(task["taskUid"])
        return len(payload)

    async def wait_for_task(self, task_uid: int, timeout: float = 60) -> dict[str, Any]:
        try:
            async with asyncio.timeout(timeout):
                return await self._poll_task(task_uid)
        except TimeoutError as error:
            raise MeilisearchError(f"Meilisearch task {task_uid} timed out") from error

    async def _poll_task(self, task_uid: int) -> dict[str, Any]:
        while True:
            task = await self._request("GET", f"/tasks/{task_uid}")
            status = task.get("status")
            if status == "succeeded":
                return task
            if status in TERMINAL_FAILURES:
                raise MeilisearchError(f"Meilisearch task {task_uid} {status}")
            await asyncio.sleep(0.2)
