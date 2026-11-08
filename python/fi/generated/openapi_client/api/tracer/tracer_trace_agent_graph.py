from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_agent_graph_response import TraceAgentGraphResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID,
    filters: str | Unset = "[]",
    refresh: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["filters"] = filters

    params["refresh"] = refresh

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/agent_graph/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse:
    if response.status_code == 200:
        response_200 = TraceAgentGraphResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ApiErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    refresh: bool | Unset = False,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse]:
    """Return one cached exact Agent Graph.

     ``path_edges`` remains an empty compatibility field until telemetry
    records authoritative chronological execution transitions.

    Pagination: no supported paging parameters.

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        filters=filters,
        refresh=refresh,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    refresh: bool | Unset = False,
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse | None:
    """Return one cached exact Agent Graph.

     ``path_edges`` remains an empty compatibility field until telemetry
    records authoritative chronological execution transitions.

    Pagination: no supported paging parameters.

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        filters=filters,
        refresh=refresh,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    refresh: bool | Unset = False,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse]:
    """Return one cached exact Agent Graph.

     ``path_edges`` remains an empty compatibility field until telemetry
    records authoritative chronological execution transitions.

    Pagination: no supported paging parameters.

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        filters=filters,
        refresh=refresh,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    refresh: bool | Unset = False,
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse | None:
    """Return one cached exact Agent Graph.

     ``path_edges`` remains an empty compatibility field until telemetry
    records authoritative chronological execution transitions.

    Pagination: no supported paging parameters.

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        refresh (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceAgentGraphResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            filters=filters,
            refresh=refresh,
        )
    ).parsed
