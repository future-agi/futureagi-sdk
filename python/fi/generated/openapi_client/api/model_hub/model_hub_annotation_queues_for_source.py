from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_annotation_queues_for_source_source_type import (
    ModelHubAnnotationQueuesForSourceSourceType,
)
from ...models.queue_for_source_response import QueueForSourceResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubAnnotationQueuesForSourceSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    sources: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_source_type: str | Unset = UNSET
    if not isinstance(source_type, Unset):
        json_source_type = source_type.value

    params["source_type"] = json_source_type

    params["source_id"] = source_id

    params["sources"] = sources

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/for-source/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse:
    if response.status_code == 200:
        response_200 = QueueForSourceResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ApiTextErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse
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
    source_type: ModelHubAnnotationQueuesForSourceSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    sources: str | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse
]:
    """Find annotation queues for a given source that the current user can annotate.
    Includes queues where:
    - The source is a queue item AND the user is an annotator in that queue
      (regardless of whether the item is explicitly assigned to them)

    Query params:
      - source_type, source_id  (single source)
      - OR sources (JSON array of {source_type, source_id} objects for multi-source lookup)

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubAnnotationQueuesForSourceSourceType | Unset):
        source_id (str | Unset):
        sources (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        sources=sources,
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
    source_type: ModelHubAnnotationQueuesForSourceSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    sources: str | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse | None:
    """Find annotation queues for a given source that the current user can annotate.
    Includes queues where:
    - The source is a queue item AND the user is an annotator in that queue
      (regardless of whether the item is explicitly assigned to them)

    Query params:
      - source_type, source_id  (single source)
      - OR sources (JSON array of {source_type, source_id} objects for multi-source lookup)

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubAnnotationQueuesForSourceSourceType | Unset):
        source_id (str | Unset):
        sources (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        sources=sources,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubAnnotationQueuesForSourceSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    sources: str | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse
]:
    """Find annotation queues for a given source that the current user can annotate.
    Includes queues where:
    - The source is a queue item AND the user is an annotator in that queue
      (regardless of whether the item is explicitly assigned to them)

    Query params:
      - source_type, source_id  (single source)
      - OR sources (JSON array of {source_type, source_id} objects for multi-source lookup)

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubAnnotationQueuesForSourceSourceType | Unset):
        source_id (str | Unset):
        sources (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        sources=sources,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubAnnotationQueuesForSourceSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    sources: str | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse | None:
    """Find annotation queues for a given source that the current user can annotate.
    Includes queues where:
    - The source is a queue item AND the user is an annotator in that queue
      (regardless of whether the item is explicitly assigned to them)

    Query params:
      - source_type, source_id  (single source)
      - OR sources (JSON array of {source_type, source_id} objects for multi-source lookup)

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubAnnotationQueuesForSourceSourceType | Unset):
        source_id (str | Unset):
        sources (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueForSourceResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            source_type=source_type,
            source_id=source_id,
            sources=sources,
        )
    ).parsed
