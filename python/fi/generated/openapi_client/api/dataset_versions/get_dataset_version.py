from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.contract_extension_management_api_error_response import (
    ContractExtensionManagementAPIErrorResponse,
)
from ...models.contract_extension_model_hub_error_response import (
    ContractExtensionModelHubErrorResponse,
)
from ...models.dataset_version_detail_response import DatasetVersionDetailResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_id: str,
    version_id: str,
    *,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/datasets/{dataset_id}/versions/{version_id}/".format(
            dataset_id=quote(str(dataset_id), safe=""),
            version_id=quote(str(version_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
):
    if response.status_code == 200:
        response_200 = DatasetVersionDetailResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ContractExtensionModelHubErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ContractExtensionModelHubErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ContractExtensionModelHubErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ContractExtensionModelHubErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ContractExtensionModelHubErrorResponse.from_dict(response.json())

        return response_500

    response_default = ContractExtensionManagementAPIErrorResponse.from_dict(
        response.json()
    )

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> Response[
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
]:
    """Read one version and a bounded page of its provenance-bearing items.

    Pagination: limit (page size); offset (0-based).

    Args:
        dataset_id (str):
        version_id (str):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ContractExtensionManagementAPIErrorResponse | ContractExtensionModelHubErrorResponse | DatasetVersionDetailResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        version_id=version_id,
        limit=limit,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> (
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
    | None
):
    """Read one version and a bounded page of its provenance-bearing items.

    Pagination: limit (page size); offset (0-based).

    Args:
        dataset_id (str):
        version_id (str):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ContractExtensionManagementAPIErrorResponse | ContractExtensionModelHubErrorResponse | DatasetVersionDetailResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        version_id=version_id,
        client=client,
        limit=limit,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> Response[
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
]:
    """Read one version and a bounded page of its provenance-bearing items.

    Pagination: limit (page size); offset (0-based).

    Args:
        dataset_id (str):
        version_id (str):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ContractExtensionManagementAPIErrorResponse | ContractExtensionModelHubErrorResponse | DatasetVersionDetailResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        version_id=version_id,
        limit=limit,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    offset: int | Unset = 0,
) -> (
    ContractExtensionManagementAPIErrorResponse
    | ContractExtensionModelHubErrorResponse
    | DatasetVersionDetailResponse
    | None
):
    """Read one version and a bounded page of its provenance-bearing items.

    Pagination: limit (page size); offset (0-based).

    Args:
        dataset_id (str):
        version_id (str):
        limit (int | Unset):  Default: 100.
        offset (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ContractExtensionManagementAPIErrorResponse | ContractExtensionModelHubErrorResponse | DatasetVersionDetailResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            version_id=version_id,
            client=client,
            limit=limit,
            offset=offset,
        )
    ).parsed
