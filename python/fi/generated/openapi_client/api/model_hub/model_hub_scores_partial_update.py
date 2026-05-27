from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.score import Score
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: Score,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
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
) -> ManagementAPIErrorResponse | Score:
    if response.status_code == 200:
        response_200 = Score.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | Score]:
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
    body: Score,
) -> Response[ManagementAPIErrorResponse | Score]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (Score):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | Score]
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
    body: Score,
) -> ManagementAPIErrorResponse | Score | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (Score):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | Score
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
    body: Score,
) -> Response[ManagementAPIErrorResponse | Score]:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (Score):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | Score]
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
    body: Score,
) -> ManagementAPIErrorResponse | Score | None:
    """Universal Score CRUD.

     GET    /model-hub/scores/?source_type=trace&source_id=<uuid>
    POST   /model-hub/scores/                 (single score)
    POST   /model-hub/scores/bulk/            (multiple scores on one source)
    DELETE /model-hub/scores/<id>/

    Args:
        id (str):
        body (Score):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | Score
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
