from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.feed_detail_api_response import FeedDetailApiResponse
from ...models.feed_update_body import FeedUpdateBody
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    cluster_id: str,
    *,
    body: FeedUpdateBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/tracer/feed/issues/{cluster_id}/".format(
            cluster_id=quote(str(cluster_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    body: FeedUpdateBody,
) -> Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        body (FeedUpdateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: FeedUpdateBody,
) -> ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse | None:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        body (FeedUpdateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        cluster_id=cluster_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: FeedUpdateBody,
) -> Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        body (FeedUpdateBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    cluster_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: FeedUpdateBody,
) -> ApiErrorResponse | FeedDetailApiResponse | ManagementAPIErrorResponse | None:
    """GET + PATCH /tracer/feed/issues/{cluster_id}/

    Args:
        cluster_id (str):
        body (FeedUpdateBody):

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
            body=body,
        )
    ).parsed
