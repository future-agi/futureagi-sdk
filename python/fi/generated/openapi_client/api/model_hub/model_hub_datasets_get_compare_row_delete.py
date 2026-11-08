from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.compare_dataset_delete_response import CompareDatasetDeleteResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    compare_id: str,
    row_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/model-hub/datasets/get-compare-row/{compare_id}/{row_id}/".format(
            compare_id=quote(str(compare_id), safe=""),
            row_id=quote(str(row_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = CompareDatasetDeleteResponse.from_dict(response.json())

        return response_200

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
    CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    compare_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        compare_id (str):
        row_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        compare_id=compare_id,
        row_id=row_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    compare_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CompareDatasetDeleteResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """
    Args:
        compare_id (str):
        row_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        compare_id=compare_id,
        row_id=row_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    compare_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        compare_id (str):
        row_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        compare_id=compare_id,
        row_id=row_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    compare_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CompareDatasetDeleteResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """
    Args:
        compare_id (str):
        row_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CompareDatasetDeleteResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            compare_id=compare_id,
            row_id=row_id,
            client=client,
        )
    ).parsed
