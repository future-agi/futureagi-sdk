from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.call_execution_delete_response import CallExecutionDeleteResponse
from ...models.call_execution_error_response import CallExecutionErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    call_execution_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/simulate/call-executions/{call_execution_id}/delete/".format(
            call_execution_id=quote(str(call_execution_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
):
    if response.status_code == 204:
        response_204 = CallExecutionDeleteResponse.from_dict(response.json())

        return response_204

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
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
]:
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
) -> Response[
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
]:
    """Delete a specific call execution

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionDeleteResponse | CallExecutionErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Delete a specific call execution

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionDeleteResponse | CallExecutionErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        call_execution_id=call_execution_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
]:
    """Delete a specific call execution

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CallExecutionDeleteResponse | CallExecutionErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        call_execution_id=call_execution_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    call_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CallExecutionDeleteResponse
    | CallExecutionErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Delete a specific call execution

    Args:
        call_execution_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CallExecutionDeleteResponse | CallExecutionErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            call_execution_id=call_execution_id,
            client=client,
        )
    ).parsed
