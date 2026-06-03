from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.simulator_agent_list_response import SimulatorAgentListResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/simulator-agents/",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
):
    if response.status_code == 200:
        response_200 = SimulatorAgentListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
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
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
]:
    """List simulator agents with pagination and search

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgentListResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
    | None
):
    """List simulator agents with pagination and search

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgentListResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
]:
    """List simulator agents with pagination and search

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgentListResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulatorAgentListResponse
    | None
):
    """List simulator agents with pagination and search

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulatorAgentListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
