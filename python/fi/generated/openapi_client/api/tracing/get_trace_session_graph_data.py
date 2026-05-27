from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_session_graph_data_request import TraceSessionGraphDataRequest
from ...types import Response


def _get_kwargs(
    *,
    body: TraceSessionGraphDataRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tracer/trace-session/get_session_graph_data/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | TraceSessionGraphDataRequest:
    if response.status_code == 201:
        response_201 = TraceSessionGraphDataRequest.from_dict(response.json())

        return response_201

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ManagementAPIErrorResponse | TraceSessionGraphDataRequest]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceSessionGraphDataRequest,
) -> Response[ManagementAPIErrorResponse | TraceSessionGraphDataRequest]:
    """Fetch time-series session metrics for the observe graph.

     Supports the same metric types as the trace graph endpoint:
    - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,
      avg_duration, avg_traces_per_session — all aggregated at session level
    - EVAL: eval scores averaged across sessions
    - ANNOTATION: annotation scores averaged across sessions

    Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

    Args:
        body (TraceSessionGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceSessionGraphDataRequest]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TraceSessionGraphDataRequest,
) -> ManagementAPIErrorResponse | TraceSessionGraphDataRequest | None:
    """Fetch time-series session metrics for the observe graph.

     Supports the same metric types as the trace graph endpoint:
    - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,
      avg_duration, avg_traces_per_session — all aggregated at session level
    - EVAL: eval scores averaged across sessions
    - ANNOTATION: annotation scores averaged across sessions

    Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

    Args:
        body (TraceSessionGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceSessionGraphDataRequest
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TraceSessionGraphDataRequest,
) -> Response[ManagementAPIErrorResponse | TraceSessionGraphDataRequest]:
    """Fetch time-series session metrics for the observe graph.

     Supports the same metric types as the trace graph endpoint:
    - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,
      avg_duration, avg_traces_per_session — all aggregated at session level
    - EVAL: eval scores averaged across sessions
    - ANNOTATION: annotation scores averaged across sessions

    Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

    Args:
        body (TraceSessionGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | TraceSessionGraphDataRequest]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TraceSessionGraphDataRequest,
) -> ManagementAPIErrorResponse | TraceSessionGraphDataRequest | None:
    """Fetch time-series session metrics for the observe graph.

     Supports the same metric types as the trace graph endpoint:
    - SYSTEM_METRIC: latency, tokens, cost, error_rate, session_count,
      avg_duration, avg_traces_per_session — all aggregated at session level
    - EVAL: eval scores averaged across sessions
    - ANNOTATION: annotation scores averaged across sessions

    Response shape matches trace graph: {metric_name, data: [{timestamp, value, primary_traffic}]}

    Args:
        body (TraceSessionGraphDataRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | TraceSessionGraphDataRequest
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
