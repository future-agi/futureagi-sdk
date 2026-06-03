from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.feed_sidebar_api_response import FeedSidebarApiResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    cluster_id: str,
    *,
    trace_id: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["trace_id"] = trace_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/feed/issues/{cluster_id}/sidebar/".format(
            cluster_id=quote(str(cluster_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = FeedSidebarApiResponse.from_dict(response.json())

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
) -> Response[ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    trace_id: str | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/{cluster_id}/sidebar/

     Accepts an optional ``?trace_id=`` query param. When present, the
    trace-level sections (AI Metadata + Evaluations) are computed for
    that trace instead of the cluster's latest, keeping the sidebar in
    sync with the Overview tab's trace selection.

    Args:
        cluster_id (str):
        trace_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        trace_id=trace_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    trace_id: str | Unset = UNSET,
) -> ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/{cluster_id}/sidebar/

     Accepts an optional ``?trace_id=`` query param. When present, the
    trace-level sections (AI Metadata + Evaluations) are computed for
    that trace instead of the cluster's latest, keeping the sidebar in
    sync with the Overview tab's trace selection.

    Args:
        cluster_id (str):
        trace_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        cluster_id=cluster_id,
        client=client,
        trace_id=trace_id,
    ).parsed


async def asyncio_detailed(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    trace_id: str | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse]:
    """GET /tracer/feed/issues/{cluster_id}/sidebar/

     Accepts an optional ``?trace_id=`` query param. When present, the
    trace-level sections (AI Metadata + Evaluations) are computed for
    that trace instead of the cluster's latest, keeping the sidebar in
    sync with the Overview tab's trace selection.

    Args:
        cluster_id (str):
        trace_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        trace_id=trace_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    trace_id: str | Unset = UNSET,
) -> ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse | None:
    """GET /tracer/feed/issues/{cluster_id}/sidebar/

     Accepts an optional ``?trace_id=`` query param. When present, the
    trace-level sections (AI Metadata + Evaluations) are computed for
    that trace instead of the cluster's latest, keeping the sidebar in
    sync with the Overview tab's trace selection.

    Args:
        cluster_id (str):
        trace_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedSidebarApiResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            cluster_id=cluster_id,
            client=client,
            trace_id=trace_id,
        )
    ).parsed
