from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.error_response import ErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.test_execution_column_order import TestExecutionColumnOrder
from ...models.test_execution_column_order_response import (
    TestExecutionColumnOrderResponse,
)
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
    *,
    body: TestExecutionColumnOrder,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/simulate/test-executions/{test_execution_id}/column-order/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
):
    if response.status_code == 200:
        response_200 = TestExecutionColumnOrderResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
]:
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
    body: TestExecutionColumnOrder,
) -> Response[
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
]:
    """Update column order for a test execution

    Args:
        test_execution_id (str):
        body (TestExecutionColumnOrder):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionColumnOrderResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionColumnOrder,
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
    | None
):
    """Update column order for a test execution

    Args:
        test_execution_id (str):
        body (TestExecutionColumnOrder):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionColumnOrderResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionColumnOrder,
) -> Response[
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
]:
    """Update column order for a test execution

    Args:
        test_execution_id (str):
        body (TestExecutionColumnOrder):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionColumnOrderResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TestExecutionColumnOrder,
) -> (
    ApiTextErrorResponse
    | ErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionColumnOrderResponse
    | None
):
    """Update column order for a test execution

    Args:
        test_execution_id (str):
        body (TestExecutionColumnOrder):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ErrorResponse | ManagementAPIErrorResponse | TestExecutionColumnOrderResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
            body=body,
        )
    ).parsed
