from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.tracer_trace_get_trace_id_by_index_response_200 import (
    TracerTraceGetTraceIdByIndexResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_trace_id = str(trace_id)
    params["trace_id"] = json_trace_id

    json_project_version_id = str(project_version_id)
    params["project_version_id"] = json_project_version_id

    params["filters"] = filters

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/get_trace_id_by_index/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200:
    if response.status_code == 200:
        response_200 = TracerTraceGetTraceIdByIndexResponse200.from_dict(
            response.json()
        )

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200]:
    """Get the previous and next trace id by index using efficient database queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200 | None:
    """Get the previous and next trace id by index using efficient database queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200]:
    """Get the previous and next trace id by index using efficient database queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        trace_id=trace_id,
        project_version_id=project_version_id,
        filters=filters,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    trace_id: UUID,
    project_version_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200 | None:
    """Get the previous and next trace id by index using efficient database queries.

    Args:
        page (int | Unset):
        limit (int | Unset):
        trace_id (UUID):
        project_version_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceGetTraceIdByIndexResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            trace_id=trace_id,
            project_version_id=project_version_id,
            filters=filters,
        )
    ).parsed
