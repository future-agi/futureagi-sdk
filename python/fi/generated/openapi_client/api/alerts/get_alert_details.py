from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.user_alert_monitor import UserAlertMonitor
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    page_number: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page_number"] = page_number

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/user-alerts/{id}/details/".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | UserAlertMonitor:
    if response.status_code == 200:
        response_200 = UserAlertMonitor.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | UserAlertMonitor]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | UserAlertMonitor]:
    """

    Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs
    list.

    Args:
        id (str):
        page_number (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | UserAlertMonitor]
    """

    kwargs = _get_kwargs(
        id=id,
        page_number=page_number,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | UserAlertMonitor | None:
    """

    Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs
    list.

    Args:
        id (str):
        page_number (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | UserAlertMonitor
    """

    return sync_detailed(
        id=id,
        client=client,
        page_number=page_number,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | UserAlertMonitor]:
    """

    Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs
    list.

    Args:
        id (str):
        page_number (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | UserAlertMonitor]
    """

    kwargs = _get_kwargs(
        id=id,
        page_number=page_number,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | UserAlertMonitor | None:
    """

    Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs
    list.

    Args:
        id (str):
        page_number (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | UserAlertMonitor
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            page_number=page_number,
            page_size=page_size,
        )
    ).parsed
