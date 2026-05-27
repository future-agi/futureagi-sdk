from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.dataset_table_response import DatasetTableResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_id: str,
    *,
    filters: str | Unset = "[]",
    sort: str | Unset = "[]",
    search: str | Unset = UNSET,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["filters"] = filters

    params["sort"] = sort

    params["search"] = search

    params["page_size"] = page_size

    params["current_page_index"] = current_page_index

    params["column_config_only"] = column_config_only

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/develops/{dataset_id}/get-dataset-table/".format(
            dataset_id=quote(str(dataset_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = DatasetTableResponse.from_dict(response.json())

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
    DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
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
    filters: str | Unset = "[]",
    sort: str | Unset = "[]",
    search: str | Unset = UNSET,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
) -> Response[
    DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        dataset_id (str):
        filters (str | Unset):  Default: '[]'.
        sort (str | Unset):  Default: '[]'.
        search (str | Unset):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        filters=filters,
        sort=sort,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    filters: str | Unset = "[]",
    sort: str | Unset = "[]",
    search: str | Unset = UNSET,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
) -> DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        filters (str | Unset):  Default: '[]'.
        sort (str | Unset):  Default: '[]'.
        search (str | Unset):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
        filters=filters,
        sort=sort,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    filters: str | Unset = "[]",
    sort: str | Unset = "[]",
    search: str | Unset = UNSET,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
) -> Response[
    DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        dataset_id (str):
        filters (str | Unset):  Default: '[]'.
        sort (str | Unset):  Default: '[]'.
        search (str | Unset):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        filters=filters,
        sort=sort,
        search=search,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    filters: str | Unset = "[]",
    sort: str | Unset = "[]",
    search: str | Unset = UNSET,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
) -> DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        filters (str | Unset):  Default: '[]'.
        sort (str | Unset):  Default: '[]'.
        search (str | Unset):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetTableResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
            filters=filters,
            sort=sort,
            search=search,
            page_size=page_size,
            current_page_index=current_page_index,
            column_config_only=column_config_only,
        )
    ).parsed
