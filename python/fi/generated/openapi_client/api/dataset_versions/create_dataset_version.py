from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.dataset_version_create import DatasetVersionCreate
from ...models.dataset_version_create_response import DatasetVersionCreateResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    dataset_id: str,
    *,
    body: DatasetVersionCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/datasets/{dataset_id}/versions/".format(
            dataset_id=quote(str(dataset_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 201:
        response_201 = DatasetVersionCreateResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ModelHubErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ModelHubErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ModelHubErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ModelHubErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ModelHubErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DatasetVersionCreate,
) -> Response[
    DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Create an immutable dataset snapshot from an explicit items list of at most 10,000 entries and a
    JSON request body at most 10 MiB (10,485,760 bytes). Oversized bodies return 400 before JSON
    parsing. An empty list creates an empty version; mutable dataset rows are never read implicitly.
    Requires workspace write access. Parent versions must belong to the same visible dataset. Returns
    version metadata; read items through the detail endpoint. This POST is not idempotent: every
    accepted request, including a retry, creates a fresh version.

    Args:
        dataset_id (str):
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DatasetVersionCreate,
) -> (
    DatasetVersionCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Create an immutable dataset snapshot from an explicit items list of at most 10,000 entries and a
    JSON request body at most 10 MiB (10,485,760 bytes). Oversized bodies return 400 before JSON
    parsing. An empty list creates an empty version; mutable dataset rows are never read implicitly.
    Requires workspace write access. Parent versions must belong to the same visible dataset. Returns
    version metadata; read items through the detail endpoint. This POST is not idempotent: every
    accepted request, including a retry, creates a fresh version.

    Args:
        dataset_id (str):
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DatasetVersionCreate,
) -> Response[
    DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Create an immutable dataset snapshot from an explicit items list of at most 10,000 entries and a
    JSON request body at most 10 MiB (10,485,760 bytes). Oversized bodies return 400 before JSON
    parsing. An empty list creates an empty version; mutable dataset rows are never read implicitly.
    Requires workspace write access. Parent versions must belong to the same visible dataset. Returns
    version metadata; read items through the detail endpoint. This POST is not idempotent: every
    accepted request, including a retry, creates a fresh version.

    Args:
        dataset_id (str):
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DatasetVersionCreate,
) -> (
    DatasetVersionCreateResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Create an immutable dataset snapshot from an explicit items list of at most 10,000 entries and a
    JSON request body at most 10 MiB (10,485,760 bytes). Oversized bodies return 400 before JSON
    parsing. An empty list creates an empty version; mutable dataset rows are never read implicitly.
    Requires workspace write access. Parent versions must belong to the same visible dataset. Returns
    version metadata; read items through the detail endpoint. This POST is not idempotent: every
    accepted request, including a retry, creates a fresh version.

    Args:
        dataset_id (str):
        body (DatasetVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetVersionCreateResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
            body=body,
        )
    ).parsed
