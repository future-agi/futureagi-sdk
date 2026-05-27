from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.call_execution import CallExecution
from ...models.call_execution_error_response import CallExecutionErrorResponse
from ...models.call_execution_status_update import CallExecutionStatusUpdate
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    call_execution_id: str,
    *,
    body: CallExecutionStatusUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/simulate/call-executions/{call_execution_id}/".format(
            call_execution_id=quote(str(call_execution_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = CallExecution.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = CallExecutionErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CallExecutionStatusUpdate,
) -> Response[CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse]:
    """Update the status of a specific call execution

    Args:
        call_execution_id (str):
        body (CallExecutionStatusUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CallExecutionStatusUpdate,
) -> CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse | None:
    """Update the status of a specific call execution

    Args:
        call_execution_id (str):
        body (CallExecutionStatusUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        call_execution_id=call_execution_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CallExecutionStatusUpdate,
) -> Response[CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse]:
    """Update the status of a specific call execution

    Args:
        call_execution_id (str):
        body (CallExecutionStatusUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CallExecutionStatusUpdate,
) -> CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse | None:
    """Update the status of a specific call execution

    Args:
        call_execution_id (str):
        body (CallExecutionStatusUpdate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecution | CallExecutionErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            call_execution_id=call_execution_id,
            client=client,
            body=body,
        )
    ).parsed
