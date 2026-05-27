from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.call_execution_error_response import CallExecutionErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_call_executions_response import RunTestCallExecutionsResponse
from ...types import Response


def _get_kwargs(
    run_test_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/run-tests/{run_test_id}/call-executions/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
):
    if response.status_code == 200:
        response_200 = RunTestCallExecutionsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = CallExecutionErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = CallExecutionErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
]:
    """Get all call executions for a specific run test with pagination and search
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status
    - limit: number of call executions per page (default: 10)
    - page: page number for call executions (default: 1)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionErrorResponse | ManagementAPIErrorResponse | RunTestCallExecutionsResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
    | None
):
    """Get all call executions for a specific run test with pagination and search
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status
    - limit: number of call executions per page (default: 10)
    - page: page number for call executions (default: 1)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionErrorResponse | ManagementAPIErrorResponse | RunTestCallExecutionsResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
]:
    """Get all call executions for a specific run test with pagination and search
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status
    - limit: number of call executions per page (default: 10)
    - page: page number for call executions (default: 1)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionErrorResponse | ManagementAPIErrorResponse | RunTestCallExecutionsResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | RunTestCallExecutionsResponse
    | None
):
    """Get all call executions for a specific run test with pagination and search
    Query Parameters:
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status
    - limit: number of call executions per page (default: 10)
    - page: page number for call executions (default: 1)

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionErrorResponse | ManagementAPIErrorResponse | RunTestCallExecutionsResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
        )
    ).parsed
