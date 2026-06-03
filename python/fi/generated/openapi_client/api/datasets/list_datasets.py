from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.dataset_list_response import DatasetListResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search_text: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 10,
    sort: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["search_text"] = search_text

    params["page"] = page

    params["page_size"] = page_size

    params["sort"] = sort

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/develops/get-datasets/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = DatasetListResponse.from_dict(response.json())

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
) -> Response[DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    search_text: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 10,
    sort: str | Unset = UNSET,
) -> Response[DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    """
    Args:
        search_text (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 10.
        sort (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        search_text=search_text,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    search_text: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 10,
    sort: str | Unset = UNSET,
) -> DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        search_text (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 10.
        sort (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        client=client,
        search_text=search_text,
        page=page,
        page_size=page_size,
        sort=sort,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search_text: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 10,
    sort: str | Unset = UNSET,
) -> Response[DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    """
    Args:
        search_text (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 10.
        sort (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        search_text=search_text,
        page=page,
        page_size=page_size,
        sort=sort,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search_text: str | Unset = "",
    page: int | Unset = 0,
    page_size: int | Unset = 10,
    sort: str | Unset = UNSET,
) -> DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        search_text (str | Unset):  Default: ''.
        page (int | Unset):  Default: 0.
        page_size (int | Unset):  Default: 10.
        sort (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DatasetListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            search_text=search_text,
            page=page,
            page_size=page_size,
            sort=sort,
        )
    ).parsed
