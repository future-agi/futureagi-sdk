from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_error_response import RunTestErrorResponse
from ...models.run_test_response import RunTestResponse
from ...models.simulate_api_run_tests_list_simulation_type import (
    SimulateApiRunTestsListSimulationType,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: str | Unset = "",
    simulation_type: SimulateApiRunTestsListSimulationType | Unset = UNSET,
    prompt_template_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search"] = search

    json_simulation_type: str | Unset = UNSET
    if not isinstance(simulation_type, Unset):
        json_simulation_type = simulation_type.value

    params["simulation_type"] = json_simulation_type

    json_prompt_template_id: str | Unset = UNSET
    if not isinstance(prompt_template_id, Unset):
        json_prompt_template_id = str(prompt_template_id)
    params["prompt_template_id"] = json_prompt_template_id

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/api/run-tests/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = RunTestResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 404:
        response_404 = RunTestErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = RunTestErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]
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
    simulation_type: SimulateApiRunTestsListSimulationType | Unset = UNSET,
    prompt_template_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]
]:
    """Get paginated list of run tests for the user's organization
    Query Parameters:
    - search: search string to filter run tests by name
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        simulation_type (SimulateApiRunTestsListSimulationType | Unset):
        prompt_template_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]]
    """

    kwargs = _get_kwargs(
        search=search,
        simulation_type=simulation_type,
        prompt_template_id=prompt_template_id,
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
    simulation_type: SimulateApiRunTestsListSimulationType | Unset = UNSET,
    prompt_template_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse] | None:
    """Get paginated list of run tests for the user's organization
    Query Parameters:
    - search: search string to filter run tests by name
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        simulation_type (SimulateApiRunTestsListSimulationType | Unset):
        prompt_template_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]
    """

    return sync_detailed(
        client=client,
        search=search,
        simulation_type=simulation_type,
        prompt_template_id=prompt_template_id,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    simulation_type: SimulateApiRunTestsListSimulationType | Unset = UNSET,
    prompt_template_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> Response[
    ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]
]:
    """Get paginated list of run tests for the user's organization
    Query Parameters:
    - search: search string to filter run tests by name
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        simulation_type (SimulateApiRunTestsListSimulationType | Unset):
        prompt_template_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]]
    """

    kwargs = _get_kwargs(
        search=search,
        simulation_type=simulation_type,
        prompt_template_id=prompt_template_id,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: str | Unset = "",
    simulation_type: SimulateApiRunTestsListSimulationType | Unset = UNSET,
    prompt_template_id: UUID | Unset = UNSET,
    page: int | Unset = 1,
    limit: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse] | None:
    """Get paginated list of run tests for the user's organization
    Query Parameters:
    - search: search string to filter run tests by name
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Args:
        search (str | Unset):  Default: ''.
        simulation_type (SimulateApiRunTestsListSimulationType | Unset):
        prompt_template_id (UUID | Unset):
        page (int | Unset):  Default: 1.
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | list[RunTestResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            simulation_type=simulation_type,
            prompt_template_id=prompt_template_id,
            page=page,
            limit=limit,
        )
    ).parsed
