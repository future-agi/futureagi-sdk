from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.prompt_simulation_scenarios_response import (
    PromptSimulationScenariosResponse,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/prompt-simulations/scenarios/",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
):
    if response.status_code == 200:
        response_200 = PromptSimulationScenariosResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
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
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
]:
    """Get list of scenarios available for prompt simulations.

     Query Parameters:
    - limit: number of items per page (default: 20)
    - page: page number (default: 1)
    - search: search string to filter scenarios by name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationScenariosResponse]
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
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
    | None
):
    """Get list of scenarios available for prompt simulations.

     Query Parameters:
    - limit: number of items per page (default: 20)
    - page: page number (default: 1)
    - search: search string to filter scenarios by name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationScenariosResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
]:
    """Get list of scenarios available for prompt simulations.

     Query Parameters:
    - limit: number of items per page (default: 20)
    - page: page number (default: 1)
    - search: search string to filter scenarios by name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationScenariosResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationScenariosResponse
    | None
):
    """Get list of scenarios available for prompt simulations.

     Query Parameters:
    - limit: number of items per page (default: 20)
    - page: page number (default: 1)
    - search: search string to filter scenarios by name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationScenariosResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
