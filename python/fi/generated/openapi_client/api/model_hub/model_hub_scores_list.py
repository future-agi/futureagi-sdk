from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_scores_list_response_200 import ModelHubScoresListResponse200
from ...models.model_hub_scores_list_source_type import ModelHubScoresListSourceType
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresListSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    label_id: UUID | Unset = UNSET,
    annotator_id: UUID | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_source_type: str | Unset = UNSET
    if not isinstance(source_type, Unset):
        json_source_type = source_type.value

    params["source_type"] = json_source_type

    params["source_id"] = source_id

    json_label_id: str | Unset = UNSET
    if not isinstance(label_id, Unset):
        json_label_id = str(label_id)
    params["label_id"] = json_label_id

    json_annotator_id: str | Unset = UNSET
    if not isinstance(annotator_id, Unset):
        json_annotator_id = str(annotator_id)
    params["annotator_id"] = json_annotator_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/scores/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | ModelHubScoresListResponse200:
    if response.status_code == 200:
        response_200 = ModelHubScoresListResponse200.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | ModelHubScoresListResponse200]:
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
    source_type: ModelHubScoresListSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    label_id: UUID | Unset = UNSET,
    annotator_id: UUID | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | ModelHubScoresListResponse200]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresListSourceType | Unset):
        source_id (str | Unset):
        label_id (UUID | Unset):
        annotator_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubScoresListResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        label_id=label_id,
        annotator_id=annotator_id,
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
    source_type: ModelHubScoresListSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    label_id: UUID | Unset = UNSET,
    annotator_id: UUID | Unset = UNSET,
) -> ManagementAPIErrorResponse | ModelHubScoresListResponse200 | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresListSourceType | Unset):
        source_id (str | Unset):
        label_id (UUID | Unset):
        annotator_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubScoresListResponse200
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        label_id=label_id,
        annotator_id=annotator_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresListSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    label_id: UUID | Unset = UNSET,
    annotator_id: UUID | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | ModelHubScoresListResponse200]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresListSourceType | Unset):
        source_id (str | Unset):
        label_id (UUID | Unset):
        annotator_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | ModelHubScoresListResponse200]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
        label_id=label_id,
        annotator_id=annotator_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresListSourceType | Unset = UNSET,
    source_id: str | Unset = UNSET,
    label_id: UUID | Unset = UNSET,
    annotator_id: UUID | Unset = UNSET,
) -> ManagementAPIErrorResponse | ModelHubScoresListResponse200 | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresListSourceType | Unset):
        source_id (str | Unset):
        label_id (UUID | Unset):
        annotator_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | ModelHubScoresListResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            source_type=source_type,
            source_id=source_id,
            label_id=label_id,
            annotator_id=annotator_id,
        )
    ).parsed
