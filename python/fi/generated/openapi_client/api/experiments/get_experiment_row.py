from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.experiment_table_rows_response import ExperimentTableRowsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    experiment_id: str,
    row_id: str,
    *,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
    get_diff: bool | Unset = False,
    search: str | Unset = "",
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page_size"] = page_size

    params["current_page_index"] = current_page_index

    params["column_config_only"] = column_config_only

    params["get_diff"] = get_diff

    params["search"] = search

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/experiments/v2/{experiment_id}/rows/{row_id}/".format(
            experiment_id=quote(str(experiment_id), safe=""),
            row_id=quote(str(row_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = ExperimentTableRowsResponse.from_dict(response.json())

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

    if response.status_code == 413:
        response_413 = ModelHubErrorResponse.from_dict(response.json())

        return response_413

    if response.status_code == 422:
        response_422 = ModelHubErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = ModelHubErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ModelHubErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    experiment_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
    get_diff: bool | Unset = False,
    search: str | Unset = "",
) -> Response[
    ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """

    Pagination: page_size (page size); current_page_index (0-based).

    Args:
        experiment_id (str):
        row_id (str):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.
        get_diff (bool | Unset):  Default: False.
        search (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        experiment_id=experiment_id,
        row_id=row_id,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
        get_diff=get_diff,
        search=search,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    experiment_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
    get_diff: bool | Unset = False,
    search: str | Unset = "",
) -> (
    ExperimentTableRowsResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """

    Pagination: page_size (page size); current_page_index (0-based).

    Args:
        experiment_id (str):
        row_id (str):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.
        get_diff (bool | Unset):  Default: False.
        search (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        experiment_id=experiment_id,
        row_id=row_id,
        client=client,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
        get_diff=get_diff,
        search=search,
    ).parsed


async def asyncio_detailed(
    experiment_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
    get_diff: bool | Unset = False,
    search: str | Unset = "",
) -> Response[
    ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """

    Pagination: page_size (page size); current_page_index (0-based).

    Args:
        experiment_id (str):
        row_id (str):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.
        get_diff (bool | Unset):  Default: False.
        search (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        experiment_id=experiment_id,
        row_id=row_id,
        page_size=page_size,
        current_page_index=current_page_index,
        column_config_only=column_config_only,
        get_diff=get_diff,
        search=search,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    experiment_id: str,
    row_id: str,
    *,
    client: AuthenticatedClient | Client,
    page_size: int | Unset = 10,
    current_page_index: int | Unset = 0,
    column_config_only: bool | Unset = False,
    get_diff: bool | Unset = False,
    search: str | Unset = "",
) -> (
    ExperimentTableRowsResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """

    Pagination: page_size (page size); current_page_index (0-based).

    Args:
        experiment_id (str):
        row_id (str):
        page_size (int | Unset):  Default: 10.
        current_page_index (int | Unset):  Default: 0.
        column_config_only (bool | Unset):  Default: False.
        get_diff (bool | Unset):  Default: False.
        search (str | Unset):  Default: ''.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExperimentTableRowsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            experiment_id=experiment_id,
            row_id=row_id,
            client=client,
            page_size=page_size,
            current_page_index=current_page_index,
            column_config_only=column_config_only,
            get_diff=get_diff,
            search=search,
        )
    ).parsed
