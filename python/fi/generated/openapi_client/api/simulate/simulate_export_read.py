from http import HTTPStatus
from io import BytesIO
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.simulate_export_read_type import SimulateExportReadType
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    item_id: str,
    *,
    type_: SimulateExportReadType,
    search: str | Unset = UNSET,
    status: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_type_ = type_.value
    params["type"] = json_type_

    params["search"] = search

    params["status"] = status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/export/{item_id}/".format(
            item_id=quote(str(item_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | File | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.json()))

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiTextErrorResponse | File | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: SimulateExportReadType,
    search: str | Unset = UNSET,
    status: str | Unset = UNSET,
) -> Response[ApiTextErrorResponse | File | ManagementAPIErrorResponse]:
    """Export data as CSV based on type parameter
    Query Parameters:
    - type: 'runtest' or 'testexecution' (required)
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status

    Args:
        item_id (str):
        type_ (SimulateExportReadType):
        search (str | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | File | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        item_id=item_id,
        type_=type_,
        search=search,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: SimulateExportReadType,
    search: str | Unset = UNSET,
    status: str | Unset = UNSET,
) -> ApiTextErrorResponse | File | ManagementAPIErrorResponse | None:
    """Export data as CSV based on type parameter
    Query Parameters:
    - type: 'runtest' or 'testexecution' (required)
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status

    Args:
        item_id (str):
        type_ (SimulateExportReadType):
        search (str | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | File | ManagementAPIErrorResponse
    """

    return sync_detailed(
        item_id=item_id,
        client=client,
        type_=type_,
        search=search,
        status=status,
    ).parsed


async def asyncio_detailed(
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: SimulateExportReadType,
    search: str | Unset = UNSET,
    status: str | Unset = UNSET,
) -> Response[ApiTextErrorResponse | File | ManagementAPIErrorResponse]:
    """Export data as CSV based on type parameter
    Query Parameters:
    - type: 'runtest' or 'testexecution' (required)
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status

    Args:
        item_id (str):
        type_ (SimulateExportReadType):
        search (str | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | File | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        item_id=item_id,
        type_=type_,
        search=search,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    item_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: SimulateExportReadType,
    search: str | Unset = UNSET,
    status: str | Unset = UNSET,
) -> ApiTextErrorResponse | File | ManagementAPIErrorResponse | None:
    """Export data as CSV based on type parameter
    Query Parameters:
    - type: 'runtest' or 'testexecution' (required)
    - search: search string to filter call executions by phone number or scenario name
    - status: filter by call execution status

    Args:
        item_id (str):
        type_ (SimulateExportReadType):
        search (str | Unset):
        status (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | File | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            item_id=item_id,
            client=client,
            type_=type_,
            search=search,
            status=status,
        )
    ).parsed
