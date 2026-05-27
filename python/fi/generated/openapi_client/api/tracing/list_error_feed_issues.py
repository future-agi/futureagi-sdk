from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.feed_list_api_response import FeedListApiResponse
from ...models.list_error_feed_issues_sort_by import ListErrorFeedIssuesSortBy
from ...models.list_error_feed_issues_sort_dir import ListErrorFeedIssuesSortDir
from ...models.list_error_feed_issues_source import ListErrorFeedIssuesSource
from ...models.list_error_feed_issues_status import ListErrorFeedIssuesStatus
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    status: ListErrorFeedIssuesStatus | Unset = UNSET,
    fix_layer: str | Unset = UNSET,
    source: ListErrorFeedIssuesSource | Unset = UNSET,
    issue_group: str | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
    sort_by: ListErrorFeedIssuesSortBy | Unset = ListErrorFeedIssuesSortBy.LAST_SEEN,
    sort_dir: ListErrorFeedIssuesSortDir | Unset = ListErrorFeedIssuesSortDir.DESC,
    limit: int | Unset = 25,
    offset: int | Unset = 0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params["search"] = search

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params["fix_layer"] = fix_layer

    json_source: str | Unset = UNSET
    if not isinstance(source, Unset):
        json_source = source.value

    params["source"] = json_source

    params["issue_group"] = issue_group

    params["time_range_days"] = time_range_days

    json_sort_by: str | Unset = UNSET
    if not isinstance(sort_by, Unset):
        json_sort_by = sort_by.value

    params["sort_by"] = json_sort_by

    json_sort_dir: str | Unset = UNSET
    if not isinstance(sort_dir, Unset):
        json_sort_dir = sort_dir.value

    params["sort_dir"] = json_sort_dir

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/feed/issues/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = FeedListApiResponse.from_dict(response.json())

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
) -> Response[ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse]:
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
    status: ListErrorFeedIssuesStatus | Unset = UNSET,
    fix_layer: str | Unset = UNSET,
    source: ListErrorFeedIssuesSource | Unset = UNSET,
    issue_group: str | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
    sort_by: ListErrorFeedIssuesSortBy | Unset = ListErrorFeedIssuesSortBy.LAST_SEEN,
    sort_dir: ListErrorFeedIssuesSortDir | Unset = ListErrorFeedIssuesSortDir.DESC,
    limit: int | Unset = 25,
    offset: int | Unset = 0,
) -> Response[ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        status (ListErrorFeedIssuesStatus | Unset):
        fix_layer (str | Unset):
        source (ListErrorFeedIssuesSource | Unset):
        issue_group (str | Unset):
        time_range_days (int | Unset):
        sort_by (ListErrorFeedIssuesSortBy | Unset):  Default:
            ListErrorFeedIssuesSortBy.LAST_SEEN.
        sort_dir (ListErrorFeedIssuesSortDir | Unset):  Default: ListErrorFeedIssuesSortDir.DESC.
        limit (int | Unset):  Default: 25.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        search=search,
        status=status,
        fix_layer=fix_layer,
        source=source,
        issue_group=issue_group,
        time_range_days=time_range_days,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
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
    status: ListErrorFeedIssuesStatus | Unset = UNSET,
    fix_layer: str | Unset = UNSET,
    source: ListErrorFeedIssuesSource | Unset = UNSET,
    issue_group: str | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
    sort_by: ListErrorFeedIssuesSortBy | Unset = ListErrorFeedIssuesSortBy.LAST_SEEN,
    sort_dir: ListErrorFeedIssuesSortDir | Unset = ListErrorFeedIssuesSortDir.DESC,
    limit: int | Unset = 25,
    offset: int | Unset = 0,
) -> ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        status (ListErrorFeedIssuesStatus | Unset):
        fix_layer (str | Unset):
        source (ListErrorFeedIssuesSource | Unset):
        issue_group (str | Unset):
        time_range_days (int | Unset):
        sort_by (ListErrorFeedIssuesSortBy | Unset):  Default:
            ListErrorFeedIssuesSortBy.LAST_SEEN.
        sort_dir (ListErrorFeedIssuesSortDir | Unset):  Default: ListErrorFeedIssuesSortDir.DESC.
        limit (int | Unset):  Default: 25.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        project_id=project_id,
        search=search,
        status=status,
        fix_layer=fix_layer,
        source=source,
        issue_group=issue_group,
        time_range_days=time_range_days,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    status: ListErrorFeedIssuesStatus | Unset = UNSET,
    fix_layer: str | Unset = UNSET,
    source: ListErrorFeedIssuesSource | Unset = UNSET,
    issue_group: str | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
    sort_by: ListErrorFeedIssuesSortBy | Unset = ListErrorFeedIssuesSortBy.LAST_SEEN,
    sort_dir: ListErrorFeedIssuesSortDir | Unset = ListErrorFeedIssuesSortDir.DESC,
    limit: int | Unset = 25,
    offset: int | Unset = 0,
) -> Response[ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        status (ListErrorFeedIssuesStatus | Unset):
        fix_layer (str | Unset):
        source (ListErrorFeedIssuesSource | Unset):
        issue_group (str | Unset):
        time_range_days (int | Unset):
        sort_by (ListErrorFeedIssuesSortBy | Unset):  Default:
            ListErrorFeedIssuesSortBy.LAST_SEEN.
        sort_dir (ListErrorFeedIssuesSortDir | Unset):  Default: ListErrorFeedIssuesSortDir.DESC.
        limit (int | Unset):  Default: 25.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        search=search,
        status=status,
        fix_layer=fix_layer,
        source=source,
        issue_group=issue_group,
        time_range_days=time_range_days,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
    search: str | Unset = UNSET,
    status: ListErrorFeedIssuesStatus | Unset = UNSET,
    fix_layer: str | Unset = UNSET,
    source: ListErrorFeedIssuesSource | Unset = UNSET,
    issue_group: str | Unset = UNSET,
    time_range_days: int | Unset = UNSET,
    sort_by: ListErrorFeedIssuesSortBy | Unset = ListErrorFeedIssuesSortBy.LAST_SEEN,
    sort_dir: ListErrorFeedIssuesSortDir | Unset = ListErrorFeedIssuesSortDir.DESC,
    limit: int | Unset = 25,
    offset: int | Unset = 0,
) -> ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/ — paginated cluster list with filters/sort.

    Args:
        project_id (UUID | Unset):
        search (str | Unset):
        status (ListErrorFeedIssuesStatus | Unset):
        fix_layer (str | Unset):
        source (ListErrorFeedIssuesSource | Unset):
        issue_group (str | Unset):
        time_range_days (int | Unset):
        sort_by (ListErrorFeedIssuesSortBy | Unset):  Default:
            ListErrorFeedIssuesSortBy.LAST_SEEN.
        sort_dir (ListErrorFeedIssuesSortDir | Unset):  Default: ListErrorFeedIssuesSortDir.DESC.
        limit (int | Unset):  Default: 25.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedListApiResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            project_id=project_id,
            search=search,
            status=status,
            fix_layer=fix_layer,
            source=source,
            issue_group=issue_group,
            time_range_days=time_range_days,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
    ).parsed
