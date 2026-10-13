from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.simulator_agent import SimulatorAgent
from ...types import Response


def _get_kwargs(
    agent_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/simulator-agents/{agent_id}/".format(
            agent_id=quote(str(agent_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent:
    if response.status_code == 200:
        response_200 = SimulatorAgent.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent
]:
    """Get details of a specific simulator agent

    Args:
        agent_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent | None:
    """Get details of a specific simulator agent

    Args:
        agent_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent
    """

    return sync_detailed(
        agent_id=agent_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent
]:
    """Get details of a specific simulator agent

    Args:
        agent_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent | None:
    """Get details of a specific simulator agent

    Args:
        agent_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgent
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            client=client,
        )
    ).parsed
