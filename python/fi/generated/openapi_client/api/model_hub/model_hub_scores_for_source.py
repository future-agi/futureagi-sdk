from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_scores_for_source_source_type import (
    ModelHubScoresForSourceSourceType,
)
from ...models.score_for_source_response import ScoreForSourceResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresForSourceSourceType,
    source_id: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    json_source_type = source_type.value
    params["source_type"] = json_source_type

    params["source_id"] = source_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/scores/for-source/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse:
    if response.status_code == 200:
        response_200 = ScoreForSourceResponse.from_dict(response.json())

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse
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
    source_type: ModelHubScoresForSourceSourceType,
    source_id: str,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse
]:
    """Get all scores for a specific source.
    GET /model-hub/scores/for-source/?source_type=trace&source_id=<uuid>

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresForSourceSourceType):
        source_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
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
    source_type: ModelHubScoresForSourceSourceType,
    source_id: str,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse | None:
    """Get all scores for a specific source.
    GET /model-hub/scores/for-source/?source_type=trace&source_id=<uuid>

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresForSourceSourceType):
        source_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresForSourceSourceType,
    source_id: str,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse
]:
    """Get all scores for a specific source.
    GET /model-hub/scores/for-source/?source_type=trace&source_id=<uuid>

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresForSourceSourceType):
        source_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        source_type=source_type,
        source_id=source_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    source_type: ModelHubScoresForSourceSourceType,
    source_id: str,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse | None:
    """Get all scores for a specific source.
    GET /model-hub/scores/for-source/?source_type=trace&source_id=<uuid>

    Args:
        page (int | Unset):
        limit (int | Unset):
        source_type (ModelHubScoresForSourceSourceType):
        source_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | ScoreForSourceResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            source_type=source_type,
            source_id=source_id,
        )
    ).parsed
