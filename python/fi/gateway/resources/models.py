"""Models resource — list and retrieve available models."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway.types.model import Model, ModelList


class Models:
    """Sync models resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def list(self) -> ModelList:
        """List all available models. GET /v1/models."""
        opts = RequestOptions(method="GET", url="/v1/models")
        return self._client._get_base_client()._request_with_retry(opts, ModelList)

    def retrieve(self, model_id: str) -> Model:
        """Retrieve a single model. GET /v1/models/{model_id}."""
        opts = RequestOptions(method="GET", url=f"/v1/models/{model_id}")
        return self._client._get_base_client()._request_with_retry(opts, Model)


class AsyncModels:
    """Async models resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def list(self) -> ModelList:
        """List all available models. GET /v1/models."""
        opts = RequestOptions(method="GET", url="/v1/models")
        return await self._client._get_base_client()._request_with_retry(opts, ModelList)

    async def retrieve(self, model_id: str) -> Model:
        """Retrieve a single model. GET /v1/models/{model_id}."""
        opts = RequestOptions(method="GET", url=f"/v1/models/{model_id}")
        return await self._client._get_base_client()._request_with_retry(opts, Model)
