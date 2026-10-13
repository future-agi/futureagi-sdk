from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.feed_stats_api_response import FeedStatsApiResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["time_range_days"] = time_range_days

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/feed/issues/stats/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = FeedStatsApiResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ApiErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse]:
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
    time_range_days: int | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/stats/ — top stats bar totals.

    Args:
        project_id (UUID | Unset):
        time_range_days (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        time_range_days=time_range_days,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
) -> ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/stats/ — top stats bar totals.

    Args:
        project_id (UUID | Unset):
        time_range_days (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        time_range_days=time_range_days,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/stats/ — top stats bar totals.

    Args:
        project_id (UUID | Unset):
        time_range_days (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        time_range_days=time_range_days,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
) -> ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/stats/ — top stats bar totals.

    Args:
        project_id (UUID | Unset):
        time_range_days (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedStatsApiResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            time_range_days=time_range_days,
        )
    ).parsed
