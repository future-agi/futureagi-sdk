"""Rerank resource -- rerank documents by relevance to a query."""

from __future__ import annotations

from typing import Any

from fi.gateway._base_client import RequestOptions
from fi.gateway._constants import NOT_GIVEN
from fi.gateway.types.rerank import RerankResponse


class Rerank:
    """Sync rerank resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        query: str,
        documents: list[str],
        top_n: Any = NOT_GIVEN,
        return_documents: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> RerankResponse:
        body: dict[str, Any] = {"model": model, "query": query, "documents": documents}
        if top_n is not NOT_GIVEN:
            body["top_n"] = top_n
        if return_documents is not NOT_GIVEN:
            body["return_documents"] = return_documents
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/rerank",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return self._client._get_base_client()._request_with_retry(opts, RerankResponse)


class AsyncRerank:
    """Async rerank resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self,
        *,
        model: str,
        query: str,
        documents: list[str],
        top_n: Any = NOT_GIVEN,
        return_documents: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_body: dict[str, Any] | None = None,
        timeout: Any = NOT_GIVEN,
        **kwargs: Any,
    ) -> RerankResponse:
        body: dict[str, Any] = {"model": model, "query": query, "documents": documents}
        if top_n is not NOT_GIVEN:
            body["top_n"] = top_n
        if return_documents is not NOT_GIVEN:
            body["return_documents"] = return_documents
        if extra_body:
            body.update(extra_body)
        if kwargs:
            body.update(kwargs)

        from fi.gateway._utils import parse_timeout

        opts = RequestOptions(
            method="POST",
            url="/v1/rerank",
            body=body,
            headers=extra_headers or {},
            timeout=parse_timeout(timeout) if timeout is not NOT_GIVEN else None,
        )
        return await self._client._get_base_client()._request_with_retry(opts, RerankResponse)
