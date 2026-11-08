from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.page_depth_exceeded_error import PageDepthExceededError
from ...models.trace_voice_call_list_response import TraceVoiceCallListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID,
    filters: str | Unset = "[]",
    attribute_keys: str | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 30,
    remove_simulation_calls: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    allow_sampled: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["filters"] = filters

    params["attribute_keys"] = attribute_keys

    params["page"] = page

    params["page_size"] = page_size

    params["remove_simulation_calls"] = remove_simulation_calls

    params["cursor"] = cursor

    params["cursor_mode"] = cursor_mode

    params["allow_sampled"] = allow_sampled

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/list_voice_calls/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
):
    if response.status_code == 200:
        response_200 = TraceVoiceCallListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PageDepthExceededError.from_dict(response.json())

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
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
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
    project_id: UUID,
    filters: str | Unset = "[]",
    attribute_keys: str | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 30,
    remove_simulation_calls: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    allow_sampled: bool | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
]:
    """List voice/conversation traces for a project in an optimized way and
    return a response similar to the provided call object schema.

    Query params:
    - project_id (required)
    - page (1-based, optional, default 1)
    - page_size (optional, default 30)

    Pagination: page (1-based); page_size (page size); cursor (opaque continuation token); cursor_mode
    (enable cursor pagination).

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        attribute_keys (str | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 30.
        remove_simulation_calls (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceVoiceCallListResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        filters=filters,
        attribute_keys=attribute_keys,
        page=page,
        page_size=page_size,
        remove_simulation_calls=remove_simulation_calls,
        cursor=cursor,
        cursor_mode=cursor_mode,
        allow_sampled=allow_sampled,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    attribute_keys: str | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 30,
    remove_simulation_calls: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    allow_sampled: bool | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
    | None
):
    """List voice/conversation traces for a project in an optimized way and
    return a response similar to the provided call object schema.

    Query params:
    - project_id (required)
    - page (1-based, optional, default 1)
    - page_size (optional, default 30)

    Pagination: page (1-based); page_size (page size); cursor (opaque continuation token); cursor_mode
    (enable cursor pagination).

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        attribute_keys (str | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 30.
        remove_simulation_calls (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceVoiceCallListResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        filters=filters,
        attribute_keys=attribute_keys,
        page=page,
        page_size=page_size,
        remove_simulation_calls=remove_simulation_calls,
        cursor=cursor,
        cursor_mode=cursor_mode,
        allow_sampled=allow_sampled,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    attribute_keys: str | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 30,
    remove_simulation_calls: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    allow_sampled: bool | Unset = UNSET,
) -> Response[
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
]:
    """List voice/conversation traces for a project in an optimized way and
    return a response similar to the provided call object schema.

    Query params:
    - project_id (required)
    - page (1-based, optional, default 1)
    - page_size (optional, default 30)

    Pagination: page (1-based); page_size (page size); cursor (opaque continuation token); cursor_mode
    (enable cursor pagination).

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        attribute_keys (str | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 30.
        remove_simulation_calls (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceVoiceCallListResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        filters=filters,
        attribute_keys=attribute_keys,
        page=page,
        page_size=page_size,
        remove_simulation_calls=remove_simulation_calls,
        cursor=cursor,
        cursor_mode=cursor_mode,
        allow_sampled=allow_sampled,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID,
    filters: str | Unset = "[]",
    attribute_keys: str | Unset = UNSET,
    page: int | Unset = 1,
    page_size: int | Unset = 30,
    remove_simulation_calls: bool | Unset = False,
    cursor: str | Unset = UNSET,
    cursor_mode: bool | Unset = False,
    allow_sampled: bool | Unset = UNSET,
) -> (
    ApiErrorResponse
    | ManagementAPIErrorResponse
    | PageDepthExceededError
    | TraceVoiceCallListResponse
    | None
):
    """List voice/conversation traces for a project in an optimized way and
    return a response similar to the provided call object schema.

    Query params:
    - project_id (required)
    - page (1-based, optional, default 1)
    - page_size (optional, default 30)

    Pagination: page (1-based); page_size (page size); cursor (opaque continuation token); cursor_mode
    (enable cursor pagination).

    Args:
        project_id (UUID):
        filters (str | Unset):  Default: '[]'.
        attribute_keys (str | Unset):
        page (int | Unset):  Default: 1.
        page_size (int | Unset):  Default: 30.
        remove_simulation_calls (bool | Unset):  Default: False.
        cursor (str | Unset):
        cursor_mode (bool | Unset):  Default: False.
        allow_sampled (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | PageDepthExceededError | TraceVoiceCallListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            filters=filters,
            attribute_keys=attribute_keys,
            page=page,
            page_size=page_size,
            remove_simulation_calls=remove_simulation_calls,
            cursor=cursor,
            cursor_mode=cursor_mode,
            allow_sampled=allow_sampled,
        )
    ).parsed
