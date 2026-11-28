from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.score import Score
from ...models.update_score import UpdateScore
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: UpdateScore,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/model-hub/scores/{id}/".format(
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | Score:
    if response.status_code == 200:
        response_200 = Score.from_dict(response.json())

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
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | Score]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateScore,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | Score]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (UpdateScore):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | Score]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateScore,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | Score | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (UpdateScore):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | Score
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateScore,
) -> Response[ApiTextErrorResponse | ManagementAPIErrorResponse | Score]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (UpdateScore):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | Score]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateScore,
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | Score | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (UpdateScore):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | Score
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
