from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_next_item_response import QueueNextItemResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    queue_id: str,
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    exclude: str | Unset = UNSET,
    before: UUID | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["exclude"] = exclude

    json_before: str | Unset = UNSET
    if not isinstance(before, Unset):
        json_before = str(before)
    params["before"] = json_before

    params["review_status"] = review_status

    params["exclude_review_status"] = exclude_review_status

    params["include_completed"] = include_completed

    params["view_mode"] = view_mode

    params["include_all_annotations"] = include_all_annotations

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{queue_id}/items/next-item/".format(
            queue_id=quote(str(queue_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse:
    if response.status_code == 200:
        response_200 = QueueNextItemResponse.from_dict(response.json())

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    exclude: str | Unset = UNSET,
    before: UUID | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse
]:
    """Get the next or previous item in the queue.

     Query params:
      exclude: comma-separated item IDs to skip
      before:  item ID — returns the item immediately before this one in order
      review_status: optional review status filter (for reviewer queues)
      exclude_review_status: optional review status to omit (for annotator queues)
      include_completed: when true, navigation can visit completed items too

    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        exclude (str | Unset):
        before (UUID | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        include_all_annotations (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
        exclude=exclude,
        before=before,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_completed=include_completed,
        view_mode=view_mode,
        include_all_annotations=include_all_annotations,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    exclude: str | Unset = UNSET,
    before: UUID | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse | None:
    """Get the next or previous item in the queue.

     Query params:
      exclude: comma-separated item IDs to skip
      before:  item ID — returns the item immediately before this one in order
      review_status: optional review status filter (for reviewer queues)
      exclude_review_status: optional review status to omit (for annotator queues)
      include_completed: when true, navigation can visit completed items too

    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        exclude (str | Unset):
        before (UUID | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        include_all_annotations (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        client=client,
        page=page,
        limit=limit,
        exclude=exclude,
        before=before,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_completed=include_completed,
        view_mode=view_mode,
        include_all_annotations=include_all_annotations,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    exclude: str | Unset = UNSET,
    before: UUID | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse
]:
    """Get the next or previous item in the queue.

     Query params:
      exclude: comma-separated item IDs to skip
      before:  item ID — returns the item immediately before this one in order
      review_status: optional review status filter (for reviewer queues)
      exclude_review_status: optional review status to omit (for annotator queues)
      include_completed: when true, navigation can visit completed items too

    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        exclude (str | Unset):
        before (UUID | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        include_all_annotations (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        page=page,
        limit=limit,
        exclude=exclude,
        before=before,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_completed=include_completed,
        view_mode=view_mode,
        include_all_annotations=include_all_annotations,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    exclude: str | Unset = UNSET,
    before: UUID | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse | None:
    """Get the next or previous item in the queue.

     Query params:
      exclude: comma-separated item IDs to skip
      before:  item ID — returns the item immediately before this one in order
      review_status: optional review status filter (for reviewer queues)
      exclude_review_status: optional review status to omit (for annotator queues)
      include_completed: when true, navigation can visit completed items too

    Args:
        queue_id (str):
        page (int | Unset):
        limit (int | Unset):
        exclude (str | Unset):
        before (UUID | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        include_all_annotations (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueNextItemResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            client=client,
            page=page,
            limit=limit,
            exclude=exclude,
            before=before,
            review_status=review_status,
            exclude_review_status=exclude_review_status,
            include_completed=include_completed,
            view_mode=view_mode,
            include_all_annotations=include_all_annotations,
        )
    ).parsed
