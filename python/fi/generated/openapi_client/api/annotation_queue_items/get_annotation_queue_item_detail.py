from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.queue_annotate_detail_response import QueueAnnotateDetailResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    queue_id: str,
    id: UUID,
    *,
    annotator_id: UUID | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
    reserve: bool | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_annotator_id: str | Unset = UNSET
    if not isinstance(annotator_id, Unset):
        json_annotator_id = str(annotator_id)
    params["annotator_id"] = json_annotator_id

    params["include_completed"] = include_completed

    params["view_mode"] = view_mode

    params["review_status"] = review_status

    params["exclude_review_status"] = exclude_review_status

    params["include_all_annotations"] = include_all_annotations

    params["reserve"] = reserve

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/annotation-queues/{queue_id}/items/{id}/annotate-detail/".format(
            queue_id=quote(str(queue_id), safe=""),
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse:
    if response.status_code == 200:
        response_200 = QueueAnnotateDetailResponse.from_dict(response.json())

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    annotator_id: UUID | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
    reserve: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse
]:
    """Get full annotation workspace data for an item.

    Args:
        queue_id (str):
        id (UUID):
        annotator_id (UUID | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_all_annotations (bool | Unset):
        reserve (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        annotator_id=annotator_id,
        include_completed=include_completed,
        view_mode=view_mode,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_all_annotations=include_all_annotations,
        reserve=reserve,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    annotator_id: UUID | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
    reserve: bool | Unset = UNSET,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueAnnotateDetailResponse
    | None
):
    """Get full annotation workspace data for an item.

    Args:
        queue_id (str):
        id (UUID):
        annotator_id (UUID | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_all_annotations (bool | Unset):
        reserve (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        id=id,
        client=client,
        annotator_id=annotator_id,
        include_completed=include_completed,
        view_mode=view_mode,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_all_annotations=include_all_annotations,
        reserve=reserve,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    annotator_id: UUID | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
    reserve: bool | Unset = UNSET,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse
]:
    """Get full annotation workspace data for an item.

    Args:
        queue_id (str):
        id (UUID):
        annotator_id (UUID | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_all_annotations (bool | Unset):
        reserve (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        annotator_id=annotator_id,
        include_completed=include_completed,
        view_mode=view_mode,
        review_status=review_status,
        exclude_review_status=exclude_review_status,
        include_all_annotations=include_all_annotations,
        reserve=reserve,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    annotator_id: UUID | Unset = UNSET,
    include_completed: bool | Unset = UNSET,
    view_mode: str | Unset = UNSET,
    review_status: str | Unset = UNSET,
    exclude_review_status: str | Unset = UNSET,
    include_all_annotations: bool | Unset = UNSET,
    reserve: bool | Unset = UNSET,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | QueueAnnotateDetailResponse
    | None
):
    """Get full annotation workspace data for an item.

    Args:
        queue_id (str):
        id (UUID):
        annotator_id (UUID | Unset):
        include_completed (bool | Unset):
        view_mode (str | Unset):
        review_status (str | Unset):
        exclude_review_status (str | Unset):
        include_all_annotations (bool | Unset):
        reserve (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | QueueAnnotateDetailResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            id=id,
            client=client,
            annotator_id=annotator_id,
            include_completed=include_completed,
            view_mode=view_mode,
            review_status=review_status,
            exclude_review_status=exclude_review_status,
            include_all_annotations=include_all_annotations,
            reserve=reserve,
        )
    ).parsed
