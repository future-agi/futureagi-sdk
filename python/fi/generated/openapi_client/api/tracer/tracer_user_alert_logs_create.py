from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.user_alert_monitor_log_write_request import (
    UserAlertMonitorLogWriteRequest,
)
from ...models.user_alert_monitor_log_write_response import (
    UserAlertMonitorLogWriteResponse,
)
from ...types import Response


def _get_kwargs(
    *,
    body: UserAlertMonitorLogWriteRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tracer/user-alert-logs/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse:
    if response.status_code == 201:
        response_201 = UserAlertMonitorLogWriteResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiErrorResponse.from_dict(response.json())

        return response_404

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse
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
    body: UserAlertMonitorLogWriteRequest,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse
]:
    """
    Args:
        body (UserAlertMonitorLogWriteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: UserAlertMonitorLogWriteRequest,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | UserAlertMonitorLogWriteResponse
    | None
):
    """
    Args:
        body (UserAlertMonitorLogWriteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UserAlertMonitorLogWriteRequest,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse
]:
    """
    Args:
        body (UserAlertMonitorLogWriteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: UserAlertMonitorLogWriteRequest,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | UserAlertMonitorLogWriteResponse
    | None
):
    """
    Args:
        body (UserAlertMonitorLogWriteRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorLogWriteResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
