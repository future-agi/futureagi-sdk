from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.observe_graph_data_response import ObserveGraphDataResponse
from ...models.trace_graph_data_request import TraceGraphDataRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: TraceGraphDataRequest,
    allow_sampled: bool | Unset = False,
    refresh: bool | Unset = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["allow_sampled"] = allow_sampled

    params["refresh"] = refresh

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tracer/trace/get_graph_methods/",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse:
    if response.status_code == 200:
        response_200 = ObserveGraphDataResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = ApiErrorResponse.from_dict(response.json())

        return response_503

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceGraphDataRequest,
    allow_sampled: bool | Unset = False,
    refresh: bool | Unset = False,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse]:
    """Fetch data for the observe graph with optimized queries

    Args:
        allow_sampled (bool | Unset):  Default: False.
        refresh (bool | Unset):  Default: False.
        body (TraceGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        allow_sampled=allow_sampled,
        refresh=refresh,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TraceGraphDataRequest,
    allow_sampled: bool | Unset = False,
    refresh: bool | Unset = False,
) -> ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse | None:
    """Fetch data for the observe graph with optimized queries

    Args:
        allow_sampled (bool | Unset):  Default: False.
        refresh (bool | Unset):  Default: False.
        body (TraceGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        allow_sampled=allow_sampled,
        refresh=refresh,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceGraphDataRequest,
    allow_sampled: bool | Unset = False,
    refresh: bool | Unset = False,
) -> Response[ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse]:
    """Fetch data for the observe graph with optimized queries

    Args:
        allow_sampled (bool | Unset):  Default: False.
        refresh (bool | Unset):  Default: False.
        body (TraceGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        allow_sampled=allow_sampled,
        refresh=refresh,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TraceGraphDataRequest,
    allow_sampled: bool | Unset = False,
    refresh: bool | Unset = False,
) -> ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse | None:
    """Fetch data for the observe graph with optimized queries

    Args:
        allow_sampled (bool | Unset):  Default: False.
        refresh (bool | Unset):  Default: False.
        body (TraceGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | ObserveGraphDataResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            allow_sampled=allow_sampled,
            refresh=refresh,
        )
    ).parsed
