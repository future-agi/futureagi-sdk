from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.run_test_kp_is_response import RunTestKPIsResponse
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/test-executions/{test_execution_id}/kpis/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse:
    if response.status_code == 200:
        response_200 = RunTestKPIsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse]:
    """Get combined KPI values for a specific run test

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse | None:
    """Get combined KPI values for a specific run test

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse]:
    """Get combined KPI values for a specific run test

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse | None:
    """Get combined KPI values for a specific run test

    Args:
        test_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | RunTestKPIsResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
        )
    ).parsed
