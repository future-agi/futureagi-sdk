"""The adapter the core resource namespaces share (prompts, knowledge bases, scores).

Each namespace calls a generated core operation through the root client's own generated client,
so credentials, retries, timeouts, connection pools and error mapping are the root client's.
This module sits outside ``fi._core``: the platform core never imports the generated core client.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import ModuleType
from typing import Any

import httpx

from fi._core.core_http import check_redirect, invalid_json
from fi.errors import api_error
from fi.generated.openapi_client.client import Client


class JsonBody:
    """Preserve wire fields, including explicit nulls and partial-update omissions.

    Some generated action schemas describe the read serializer rather than the
    write payload. The operation still owns its HTTP method and URL.
    """

    def __init__(self, value: Mapping[str, Any]) -> None:
        self.value = dict(value)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.value)


def _kwargs(
    operation: ModuleType,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    query: Mapping[str, Any] | None,
    json: Mapping[str, Any] | None,
    files: list[tuple[str, tuple[str, bytes, str]]] | None,
) -> dict[str, Any]:
    request = operation._get_kwargs(*args, **kwargs)
    if query is not None:
        request["params"] = {
            **request.get("params", {}),
            **{k: v for k, v in query.items() if v is not None},
        }
    if json is not None:
        request["json"] = dict(json)
    if files is not None:
        request["data"] = request.pop("json", {})
        request["files"] = files
        request["headers"] = {
            k: v for k, v in request.get("headers", {}).items()
            if k.lower() != "content-type"
        }
    return request


def _result(
    response: httpx.Response, operation: ModuleType, *, unwrap_result: bool = True,
) -> Any:
    check_redirect(response, operation.__name__.rsplit(".", 1)[-1])
    if not response.content:
        payload = None
    else:
        try:
            payload = response.json()
        except ValueError:
            if response.is_success:
                raise invalid_json(response) from None
            payload = response.text
    if response.is_error:
        raise api_error(response.status_code, payload, response.headers)
    if isinstance(payload, dict) and payload.get("status") is False:
        raise api_error(400, payload, response.headers)
    if unwrap_result and isinstance(payload, dict) and "status" in payload and "result" in payload:
        return payload["result"]
    return payload


class CoreResource:
    """Reuse credentials, retries, errors, timeouts and pools from the root client."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def _request(
        self, operation: ModuleType, *args: Any,
        query: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
        unwrap_result: bool = True,
        **kwargs: Any,
    ) -> Any:
        request = _kwargs(operation, args, kwargs, query, json, files)
        response = self._client.get_httpx_client().request(**request)
        return _result(response, operation, unwrap_result=unwrap_result)


class AsyncCoreResource:
    """Async dispatch through the same generated client's async connection pool."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def _request(
        self, operation: ModuleType, *args: Any,
        query: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
        unwrap_result: bool = True,
        **kwargs: Any,
    ) -> Any:
        request = _kwargs(operation, args, kwargs, query, json, files)
        response = await self._client.get_async_httpx_client().request(**request)
        return _result(response, operation, unwrap_result=unwrap_result)
