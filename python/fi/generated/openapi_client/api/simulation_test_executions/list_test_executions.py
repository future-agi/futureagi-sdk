from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_error_response import RunTestErrorResponse
from ...models.test_execution import TestExecution
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/api/test-executions/",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = TestExecution.from_dict(response_200_item_data)

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
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]]:
    """Get paginated list of test executions for the user's organization
    Query Parameters:
    - search: search string to filter test executions by run test name
    - status: filter by execution status
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution] | None:
    """Get paginated list of test executions for the user's organization
    Query Parameters:
    - search: search string to filter test executions by run test name
    - status: filter by execution status
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]]:
    """Get paginated list of test executions for the user's organization
    Query Parameters:
    - search: search string to filter test executions by run test name
    - status: filter by execution status
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution] | None:
    """Get paginated list of test executions for the user's organization
    Query Parameters:
    - search: search string to filter test executions by run test name
    - status: filter by execution status
    - limit: number of items per page (default: 10)
    - page: page number (default: 1)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | RunTestErrorResponse | list[TestExecution]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
