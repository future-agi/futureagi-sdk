from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.simulate_api_personas_system_personas_response_200 import (
    SimulateApiPersonasSystemPersonasResponse200,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/api/personas/system/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
):
    if response.status_code == 200:
        response_200 = SimulateApiPersonasSystemPersonasResponse200.from_dict(
            response.json()
        )

        return response_200

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
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
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
]:
    """Get only system-level personas

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulateApiPersonasSystemPersonasResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
    | None
):
    """Get only system-level personas

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulateApiPersonasSystemPersonasResponse200
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> Response[
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
]:
    """Get only system-level personas

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulateApiPersonasSystemPersonasResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
) -> (
    ApiErrorWithDetailsResponse
    | ManagementAPIErrorResponse
    | SimulateApiPersonasSystemPersonasResponse200
    | None
):
    """Get only system-level personas

    Args:
        page (int | Unset):
        limit (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | SimulateApiPersonasSystemPersonasResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
        )
    ).parsed
