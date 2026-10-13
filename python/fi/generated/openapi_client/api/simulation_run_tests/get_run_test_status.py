from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.test_execution_status_summary import TestExecutionStatusSummary
from ...types import Response


def _get_kwargs(
    run_test_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/run-tests/{run_test_id}/status/".format(
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary:
    if response.status_code == 200:
        response_200 = TestExecutionStatusSummary.from_dict(response.json())

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
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary]:
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
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary]:
    """Get test execution status

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary]
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
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary | None:
    """Get test execution status

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary
    """

    return sync_detailed(
        run_test_id=run_test_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary]:
    """Get test execution status

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary]
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
) -> ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary | None:
    """Get test execution status

    Args:
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ManagementAPIErrorResponse | TestExecutionStatusSummary
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            client=client,
        )
    ).parsed
