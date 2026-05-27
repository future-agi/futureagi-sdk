from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.feed_detail_api_response import FeedDetailApiResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    cluster_id: str,
    *,
    project_id: UUID | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/feed/issues/{cluster_id}/".format(
            cluster_id=quote(str(cluster_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = FeedDetailApiResponse.from_dict(response.json())

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
) -> Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]:
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
    project_id: UUID | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        project_id=project_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
) -> ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse | None:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        cluster_id=cluster_id,
        client=client,
        project_id=project_id,
    ).parsed


async def asyncio_detailed(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
) -> Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        project_id=project_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    project_id: UUID | Unset = UNSET,
) -> ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse | None:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            cluster_id=cluster_id,
            client=client,
            project_id=project_id,
        )
    ).parsed
