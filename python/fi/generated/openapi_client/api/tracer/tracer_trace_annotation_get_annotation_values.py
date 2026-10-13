from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.get_trace_annotation_values_response import (
    GetTraceAnnotationValuesResponse,
)
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    observation_span_id: str | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    annotators: str | Unset = UNSET,
    exclude_annotators: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["page"] = page

    params["limit"] = limit

    params["observation_span_id"] = observation_span_id

    json_trace_id: str | Unset = UNSET
    if not isinstance(trace_id, Unset):
        json_trace_id = str(trace_id)
    params["trace_id"] = json_trace_id

    params["annotators"] = annotators

    params["exclude_annotators"] = exclude_annotators

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace-annotation/get_annotation_values/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = GetTraceAnnotationValuesResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    observation_span_id: str | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    annotators: str | Unset = UNSET,
    exclude_annotators: str | Unset = UNSET,
) -> Response[
    ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse
]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        observation_span_id (str | Unset):
        trace_id (UUID | Unset):
        annotators (str | Unset):
        exclude_annotators (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        observation_span_id=observation_span_id,
        trace_id=trace_id,
        annotators=annotators,
        exclude_annotators=exclude_annotators,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    observation_span_id: str | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    annotators: str | Unset = UNSET,
    exclude_annotators: str | Unset = UNSET,
) -> (
    ApiErrorResponse
    | GetTraceAnnotationValuesResponse
    | ManagementAPIErrorResponse
    | None
):
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        observation_span_id (str | Unset):
        trace_id (UUID | Unset):
        annotators (str | Unset):
        exclude_annotators (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        limit=limit,
        observation_span_id=observation_span_id,
        trace_id=trace_id,
        annotators=annotators,
        exclude_annotators=exclude_annotators,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    observation_span_id: str | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    annotators: str | Unset = UNSET,
    exclude_annotators: str | Unset = UNSET,
) -> Response[
    ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse
]:
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        observation_span_id (str | Unset):
        trace_id (UUID | Unset):
        annotators (str | Unset):
        exclude_annotators (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        limit=limit,
        observation_span_id=observation_span_id,
        trace_id=trace_id,
        annotators=annotators,
        exclude_annotators=exclude_annotators,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    observation_span_id: str | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    annotators: str | Unset = UNSET,
    exclude_annotators: str | Unset = UNSET,
) -> (
    ApiErrorResponse
    | GetTraceAnnotationValuesResponse
    | ManagementAPIErrorResponse
    | None
):
    """
    Args:
        page (int | Unset):
        limit (int | Unset):
        observation_span_id (str | Unset):
        trace_id (UUID | Unset):
        annotators (str | Unset):
        exclude_annotators (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | GetTraceAnnotationValuesResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            limit=limit,
            observation_span_id=observation_span_id,
            trace_id=trace_id,
            annotators=annotators,
            exclude_annotators=exclude_annotators,
        )
    ).parsed
