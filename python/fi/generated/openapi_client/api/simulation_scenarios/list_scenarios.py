from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.scenario_error_response import ScenarioErrorResponse
from ...models.scenario_list_response import ScenarioListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: str | Unset = "",
    agent_definition_id: UUID | Unset = UNSET,
    agent_type: str | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search"] = search

    json_agent_definition_id: str | Unset = UNSET
    if not isinstance(agent_definition_id, Unset):
        json_agent_definition_id = str(agent_definition_id)
    params["agent_definition_id"] = json_agent_definition_id

    params["agent_type"] = agent_type

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/scenarios/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse:
    if response.status_code == 200:
        response_200 = ScenarioListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ScenarioErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ScenarioErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    agent_definition_id: UUID | Unset = UNSET,
    agent_type: str | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse
]:
    """List scenarios

     Returns a paginated list of scenarios for the user's organization.

    Args:
        search (str | Unset):  Default: ''.
        agent_definition_id (UUID | Unset):
        agent_type (str | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        agent_definition_id=agent_definition_id,
        agent_type=agent_type,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    agent_definition_id: UUID | Unset = UNSET,
    agent_type: str | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse | None:
    """List scenarios

     Returns a paginated list of scenarios for the user's organization.

    Args:
        search (str | Unset):  Default: ''.
        agent_definition_id (UUID | Unset):
        agent_type (str | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse
    """

    return sync_detailed(
        client=client,
        search=search,
        agent_definition_id=agent_definition_id,
        agent_type=agent_type,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    agent_definition_id: UUID | Unset = UNSET,
    agent_type: str | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse
]:
    """List scenarios

     Returns a paginated list of scenarios for the user's organization.

    Args:
        search (str | Unset):  Default: ''.
        agent_definition_id (UUID | Unset):
        agent_type (str | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse]
    """

    kwargs = _get_kwargs(
        search=search,
        agent_definition_id=agent_definition_id,
        agent_type=agent_type,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    agent_definition_id: UUID | Unset = UNSET,
    agent_type: str | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse | None:
    """List scenarios

     Returns a paginated list of scenarios for the user's organization.

    Args:
        search (str | Unset):  Default: ''.
        agent_definition_id (UUID | Unset):
        agent_type (str | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ScenarioErrorResponse | ScenarioListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            agent_definition_id=agent_definition_id,
            agent_type=agent_type,
            page=page,
            limit=limit,
        )
    ).parsed
