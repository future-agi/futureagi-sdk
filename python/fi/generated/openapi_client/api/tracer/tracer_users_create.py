from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.users_query import UsersQuery
from ...models.users_response import UsersResponse
from ...types import Response


def _get_kwargs(
    *,
    body: UsersQuery,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tracer/users/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse:
    if response.status_code == 200:
        response_200 = UsersResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = ApiErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ApiErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UsersQuery,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination). Pass these in the request body.

    Args:
        body (UsersQuery):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]
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
    body: UsersQuery,
) -> ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse | None:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination). Pass these in the request body.

    Args:
        body (UsersQuery):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UsersQuery,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination). Pass these in the request body.

    Args:
        body (UsersQuery):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: UsersQuery,
) -> ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse | None:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination). Pass these in the request body.

    Args:
        body (UsersQuery):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
