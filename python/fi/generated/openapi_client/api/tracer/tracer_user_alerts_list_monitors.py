from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.tracer_user_alerts_list_monitors_sort_direction import (
    TracerUserAlertsListMonitorsSortDirection,
)
from ...models.tracer_user_alerts_list_monitors_status_item import (
    TracerUserAlertsListMonitorsStatusItem,
)
from ...models.user_alert_monitor_list_response import UserAlertMonitorListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    search_text: str | Unset = UNSET,
    project_id: list[UUID] | Unset = UNSET,
    status: list[TracerUserAlertsListMonitorsStatusItem] | Unset = UNSET,
    metric_type: list[str] | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_direction: TracerUserAlertsListMonitorsSortDirection | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page_number"] = page_number

    params["page_size"] = page_size

    params["search_text"] = search_text

    json_project_id: list[str] | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = []
        for project_id_item_data in project_id:
            project_id_item = str(project_id_item_data)
            json_project_id.append(project_id_item)

    params["project_id"] = json_project_id

    json_status: list[str] | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    json_metric_type: list[str] | Unset = UNSET
    if not isinstance(metric_type, Unset):
        json_metric_type = metric_type

    params["metric_type"] = json_metric_type

    params["sort_by"] = sort_by

    json_sort_direction: str | Unset = UNSET
    if not isinstance(sort_direction, Unset):
        json_sort_direction = sort_direction.value

    params["sort_direction"] = json_sort_direction

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/user-alerts/list_monitors/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse:
    if response.status_code == 200:
        response_200 = UserAlertMonitorListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse
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
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    search_text: str | Unset = UNSET,
    project_id: list[UUID] | Unset = UNSET,
    status: list[TracerUserAlertsListMonitorsStatusItem] | Unset = UNSET,
    metric_type: list[str] | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_direction: TracerUserAlertsListMonitorsSortDirection | Unset = UNSET,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse
]:
    """

    Pagination: page_number (0-based); page_size (page size).

    Args:
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        search_text (str | Unset):
        project_id (list[UUID] | Unset):
        status (list[TracerUserAlertsListMonitorsStatusItem] | Unset):
        metric_type (list[str] | Unset):
        sort_by (str | Unset):
        sort_direction (TracerUserAlertsListMonitorsSortDirection | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse]
    """

    kwargs = _get_kwargs(
        page_number=page_number,
        page_size=page_size,
        search_text=search_text,
        project_id=project_id,
        status=status,
        metric_type=metric_type,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    search_text: str | Unset = UNSET,
    project_id: list[UUID] | Unset = UNSET,
    status: list[TracerUserAlertsListMonitorsStatusItem] | Unset = UNSET,
    metric_type: list[str] | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_direction: TracerUserAlertsListMonitorsSortDirection | Unset = UNSET,
) -> (
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse | None
):
    """

    Pagination: page_number (0-based); page_size (page size).

    Args:
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        search_text (str | Unset):
        project_id (list[UUID] | Unset):
        status (list[TracerUserAlertsListMonitorsStatusItem] | Unset):
        metric_type (list[str] | Unset):
        sort_by (str | Unset):
        sort_direction (TracerUserAlertsListMonitorsSortDirection | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse
    """

    return sync_detailed(
        client=client,
        page_number=page_number,
        page_size=page_size,
        search_text=search_text,
        project_id=project_id,
        status=status,
        metric_type=metric_type,
        sort_by=sort_by,
        sort_direction=sort_direction,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    search_text: str | Unset = UNSET,
    project_id: list[UUID] | Unset = UNSET,
    status: list[TracerUserAlertsListMonitorsStatusItem] | Unset = UNSET,
    metric_type: list[str] | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_direction: TracerUserAlertsListMonitorsSortDirection | Unset = UNSET,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse
]:
    """

    Pagination: page_number (0-based); page_size (page size).

    Args:
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        search_text (str | Unset):
        project_id (list[UUID] | Unset):
        status (list[TracerUserAlertsListMonitorsStatusItem] | Unset):
        metric_type (list[str] | Unset):
        sort_by (str | Unset):
        sort_direction (TracerUserAlertsListMonitorsSortDirection | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse]
    """

    kwargs = _get_kwargs(
        page_number=page_number,
        page_size=page_size,
        search_text=search_text,
        project_id=project_id,
        status=status,
        metric_type=metric_type,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page_number: int | Unset = 0,
    page_size: int | Unset = 30,
    search_text: str | Unset = UNSET,
    project_id: list[UUID] | Unset = UNSET,
    status: list[TracerUserAlertsListMonitorsStatusItem] | Unset = UNSET,
    metric_type: list[str] | Unset = UNSET,
    sort_by: str | Unset = UNSET,
    sort_direction: TracerUserAlertsListMonitorsSortDirection | Unset = UNSET,
) -> (
    ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse | None
):
    """

    Pagination: page_number (0-based); page_size (page size).

    Args:
        page_number (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 30.
        search_text (str | Unset):
        project_id (list[UUID] | Unset):
        status (list[TracerUserAlertsListMonitorsStatusItem] | Unset):
        metric_type (list[str] | Unset):
        sort_by (str | Unset):
        sort_direction (TracerUserAlertsListMonitorsSortDirection | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | UserAlertMonitorListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page_number=page_number,
            page_size=page_size,
            search_text=search_text,
            project_id=project_id,
            status=status,
            metric_type=metric_type,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    ).parsed
