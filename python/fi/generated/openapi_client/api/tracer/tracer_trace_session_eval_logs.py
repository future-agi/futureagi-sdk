from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_session import TraceSession
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace-session/{id}/eval_logs/".format(
            id=quote(str(id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TraceSession:
    if response.status_code == 200:
        response_200 = TraceSession.from_dict(response.json())

        return response_200

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TraceSession]:
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
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | TraceSession]:
    r"""Session-scoped eval log feed for TracesDrawer's \"Evals\" tab.

     Session-level eval results are walled off from span/trace surfaces
    by ``target_type='session'`` — this endpoint is the only place
    they appear.

    Query params:
        page (int, 0-indexed, default 0)
        page_size (int, default 25, max 100)

    Pagination: page (0-based); page_size (page size).

    Args:
        id (str):
        page (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceSession]
    """

    kwargs = _get_kwargs(
        id=id,
        page=page,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | TraceSession | None:
    r"""Session-scoped eval log feed for TracesDrawer's \"Evals\" tab.

     Session-level eval results are walled off from span/trace surfaces
    by ``target_type='session'`` — this endpoint is the only place
    they appear.

    Query params:
        page (int, 0-indexed, default 0)
        page_size (int, default 25, max 100)

    Pagination: page (0-based); page_size (page size).

    Args:
        id (str):
        page (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceSession
    """

    return sync_detailed(
        id=id,
        client=client,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> Response[ManagementAPIErrorResponse | TraceSession]:
    r"""Session-scoped eval log feed for TracesDrawer's \"Evals\" tab.

     Session-level eval results are walled off from span/trace surfaces
    by ``target_type='session'`` — this endpoint is the only place
    they appear.

    Query params:
        page (int, 0-indexed, default 0)
        page_size (int, default 25, max 100)

    Pagination: page (0-based); page_size (page size).

    Args:
        id (str):
        page (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceSession]
    """

    kwargs = _get_kwargs(
        id=id,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
) -> ManagementAPIErrorResponse | TraceSession | None:
    r"""Session-scoped eval log feed for TracesDrawer's \"Evals\" tab.

     Session-level eval results are walled off from span/trace surfaces
    by ``target_type='session'`` — this endpoint is the only place
    they appear.

    Query params:
        page (int, 0-indexed, default 0)
        page_size (int, default 25, max 100)

    Pagination: page (0-based); page_size (page size).

    Args:
        id (str):
        page (int | Unset):
        page_size (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceSession
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            page=page,
            page_size=page_size,
        )
    ).parsed
