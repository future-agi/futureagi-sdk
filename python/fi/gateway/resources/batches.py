"""Batch resource — create, retrieve, cancel, and wait for batch jobs."""

from __future__ import annotations

import time
from typing import Any

import anyio

from fi.gateway._base_client import RequestOptions
from fi.gateway._exceptions import APITimeoutError
from fi.gateway.types.batch import BatchResponse


class Batches:
    """Sync batches resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        requests: list[dict[str, Any]],
        *,
        max_concurrency: int = 10,
    ) -> BatchResponse:
        """Create a batch job. POST /v1/batches."""
        body = {"requests": requests, "max_concurrency": max_concurrency}
        opts = RequestOptions(method="POST", url="/v1/batches", body=body)
        return self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    def retrieve(self, batch_id: str) -> BatchResponse:
        """Get batch status. GET /v1/batches/{batch_id}."""
        opts = RequestOptions(method="GET", url=f"/v1/batches/{batch_id}")
        return self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    def cancel(self, batch_id: str) -> BatchResponse:
        """Cancel a batch job. POST /v1/batches/{batch_id}/cancel."""
        opts = RequestOptions(method="POST", url=f"/v1/batches/{batch_id}/cancel")
        return self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    def wait(
        self,
        batch_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float = 3600.0,
    ) -> BatchResponse:
        """Poll until the batch completes or times out."""
        deadline = time.monotonic() + timeout
        while True:
            result = self.retrieve(batch_id)
            if result.status in ("completed", "failed", "cancelled"):
                return result
            if time.monotonic() >= deadline:
                msg = f"Batch {batch_id} did not complete within {timeout}s"
                raise APITimeoutError(msg)
            time.sleep(poll_interval)

    def create_and_wait(
        self,
        requests: list[dict[str, Any]],
        *,
        max_concurrency: int = 10,
        poll_interval: float = 2.0,
        timeout: float = 3600.0,
    ) -> BatchResponse:
        """Create a batch and wait for it to complete."""
        batch = self.create(requests, max_concurrency=max_concurrency)
        return self.wait(batch.batch_id, poll_interval=poll_interval, timeout=timeout)


class AsyncBatches:
    """Async batches resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        requests: list[dict[str, Any]],
        *,
        max_concurrency: int = 10,
    ) -> BatchResponse:
        """Create a batch job. POST /v1/batches."""
        body = {"requests": requests, "max_concurrency": max_concurrency}
        opts = RequestOptions(method="POST", url="/v1/batches", body=body)
        return await self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    async def retrieve(self, batch_id: str) -> BatchResponse:
        """Get batch status. GET /v1/batches/{batch_id}."""
        opts = RequestOptions(method="GET", url=f"/v1/batches/{batch_id}")
        return await self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    async def cancel(self, batch_id: str) -> BatchResponse:
        """Cancel a batch job. POST /v1/batches/{batch_id}/cancel."""
        opts = RequestOptions(method="POST", url=f"/v1/batches/{batch_id}/cancel")
        return await self._client._get_base_client()._request_with_retry(opts, BatchResponse)

    async def wait(
        self,
        batch_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float = 3600.0,
    ) -> BatchResponse:
        """Poll until the batch completes or times out."""
        deadline = time.monotonic() + timeout
        while True:
            result = await self.retrieve(batch_id)
            if result.status in ("completed", "failed", "cancelled"):
                return result
            if time.monotonic() >= deadline:
                msg = f"Batch {batch_id} did not complete within {timeout}s"
                raise APITimeoutError(msg)
            await anyio.sleep(poll_interval)

    async def create_and_wait(
        self,
        requests: list[dict[str, Any]],
        *,
        max_concurrency: int = 10,
        poll_interval: float = 2.0,
        timeout: float = 3600.0,
    ) -> BatchResponse:
        """Create a batch and wait for it to complete."""
        batch = await self.create(requests, max_concurrency=max_concurrency)
        return await self.wait(batch.batch_id, poll_interval=poll_interval, timeout=timeout)
