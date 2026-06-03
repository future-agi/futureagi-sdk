from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.tracer_trace_agent_graph_response_200 import (
    TracerTraceAgentGraphResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID,
    filters: str | Unset = "[]",
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["filters"] = filters

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/agent_graph/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200:
    if response.status_code == 200:
        response_200 = TracerTraceAgentGraphResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200]:
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
    project_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200]:
    """Return the aggregate agent graph for a project.

     Computes nodes (distinct span types/names) and edges (parent→child
    transitions) across all traces in the given time window.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_id=project_id,
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
    project_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200 | None:
    """Return the aggregate agent graph for a project.

     Computes nodes (distinct span types/names) and edges (parent→child
    transitions) across all traces in the given time window.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        project_id=project_id,
        filters=filters,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID,
    filters: str | Unset = "[]",
) -> Response[ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200]:
    """Return the aggregate agent graph for a project.

     Computes nodes (distinct span types/names) and edges (parent→child
    transitions) across all traces in the given time window.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        project_id=project_id,
        filters=filters,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    project_id: UUID,
    filters: str | Unset = "[]",
) -> ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200 | None:
    """Return the aggregate agent graph for a project.

     Computes nodes (distinct span types/names) and edges (parent→child
    transitions) across all traces in the given time window.

    Args:
        page (int | Unset):
        limit (int | Unset):
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TracerTraceAgentGraphResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            project_id=project_id,
            filters=filters,
        )
    ).parsed
