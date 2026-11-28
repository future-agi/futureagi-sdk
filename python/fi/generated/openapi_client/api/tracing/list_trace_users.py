from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.users_response import UsersResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    page_size: int | Unset = UNSET,
    current_page_index: int | Unset = UNSET,
    sort_params: str | Unset = "[]",
    filters: str | Unset = "[]",
    export: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    requested_columns: str | Unset = UNSET,
    attribute_keys: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["search"] = search

    params["page_size"] = page_size

    params["current_page_index"] = current_page_index

    params["sort_params"] = sort_params

    params["filters"] = filters

    params["export"] = export

    params["cursor"] = cursor

    params["cursor_mode"] = cursor_mode

    params["requested_columns"] = requested_columns

    params["attribute_keys"] = attribute_keys

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/users/",
        "params": params,
    }

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
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    page_size: int | Unset = UNSET,
    current_page_index: int | Unset = UNSET,
    sort_params: str | Unset = "[]",
    filters: str | Unset = "[]",
    export: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    requested_columns: str | Unset = UNSET,
    attribute_keys: str | Unset = UNSET,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        page_size (int | Unset):
        current_page_index (int | Unset):
        sort_params (str | Unset):  Default: '[]'.
        filters (str | Unset):  Default: '[]'.
        export (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        requested_columns (str | Unset):
        attribute_keys (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        sort_params=sort_params,
        filters=filters,
        export=export,
        cursor=cursor,
        cursor_mode=cursor_mode,
        requested_columns=requested_columns,
        attribute_keys=attribute_keys,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    page_size: int | Unset = UNSET,
    current_page_index: int | Unset = UNSET,
    sort_params: str | Unset = "[]",
    filters: str | Unset = "[]",
    export: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    requested_columns: str | Unset = UNSET,
    attribute_keys: str | Unset = UNSET,
) -> ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse | None:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        page_size (int | Unset):
        current_page_index (int | Unset):
        sort_params (str | Unset):  Default: '[]'.
        filters (str | Unset):  Default: '[]'.
        export (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        requested_columns (str | Unset):
        attribute_keys (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        sort_params=sort_params,
        filters=filters,
        export=export,
        cursor=cursor,
        cursor_mode=cursor_mode,
        requested_columns=requested_columns,
        attribute_keys=attribute_keys,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    page_size: int | Unset = UNSET,
    current_page_index: int | Unset = UNSET,
    sort_params: str | Unset = "[]",
    filters: str | Unset = "[]",
    export: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    requested_columns: str | Unset = UNSET,
    attribute_keys: str | Unset = UNSET,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        page_size (int | Unset):
        current_page_index (int | Unset):
        sort_params (str | Unset):  Default: '[]'.
        filters (str | Unset):  Default: '[]'.
        export (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        requested_columns (str | Unset):
        attribute_keys (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        sort_params=sort_params,
        filters=filters,
        export=export,
        cursor=cursor,
        cursor_mode=cursor_mode,
        requested_columns=requested_columns,
        attribute_keys=attribute_keys,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    page_size: int | Unset = UNSET,
    current_page_index: int | Unset = UNSET,
    sort_params: str | Unset = "[]",
    filters: str | Unset = "[]",
    export: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    requested_columns: str | Unset = UNSET,
    attribute_keys: str | Unset = UNSET,
) -> ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse | None:
    """List traces filtered by project ID with optimized queries.

    Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token);
    cursor_mode (enable cursor pagination).

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        page_size (int | Unset):
        current_page_index (int | Unset):
        sort_params (str | Unset):  Default: '[]'.
        filters (str | Unset):  Default: '[]'.
        export (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        requested_columns (str | Unset):
        attribute_keys (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UsersResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            search=search,
            page_size=page_size,
            current_page_index=current_page_index,
            sort_params=sort_params,
            filters=filters,
            export=export,
            cursor=cursor,
            cursor_mode=cursor_mode,
            requested_columns=requested_columns,
            attribute_keys=attribute_keys,
        )
    ).parsed
