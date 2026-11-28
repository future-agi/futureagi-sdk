from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_response import ApiErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.trace_voice_call_detail_response import TraceVoiceCallDetailResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    test_execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    traceId: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_test_execution_id: str | Unset = UNSET
    if not isinstance(test_execution_id, Unset):
        json_test_execution_id = str(test_execution_id)
    params["test_execution_id"] = json_test_execution_id

    json_call_execution_id: str | Unset = UNSET
    if not isinstance(call_execution_id, Unset):
        json_call_execution_id = str(call_execution_id)
    params["call_execution_id"] = json_call_execution_id

    json_trace_id: str | Unset = UNSET
    if not isinstance(trace_id, Unset):
        json_trace_id = str(trace_id)
    params["trace_id"] = json_trace_id

    json_traceId: str | Unset = UNSET
    if not isinstance(traceId, Unset):
        json_traceId = str(traceId)
    params["traceId"] = json_traceId

    json_project_id: str | Unset = UNSET
    if not isinstance(project_id, Unset):
        json_project_id = str(project_id)
    params["project_id"] = json_project_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tracer/trace/voice_call_detail/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse:
    if response.status_code == 200:
        response_200 = TraceVoiceCallDetailResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ApiErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse
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
    test_execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    traceId: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse
]:
    """Return the heavy / detail-only fields for a single voice call.

     Query params:
    - trace_id or legacy traceId (required) — UUID of the voice call trace.
    - project_id (optional) — the project the call was opened from.
    - test_execution_id or call_execution_id (optional) — a run the caller
      can read; the hidden simulation project of that run's agent is read
      in place of the caller's projects.

    Pagination: no supported paging parameters.

    Args:
        test_execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):
        trace_id (UUID | Unset):
        traceId (UUID | Unset):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        call_execution_id=call_execution_id,
        trace_id=trace_id,
        traceId=traceId,
        project_id=project_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    test_execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    traceId: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
) -> (
    ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse | None
):
    """Return the heavy / detail-only fields for a single voice call.

     Query params:
    - trace_id or legacy traceId (required) — UUID of the voice call trace.
    - project_id (optional) — the project the call was opened from.
    - test_execution_id or call_execution_id (optional) — a run the caller
      can read; the hidden simulation project of that run's agent is read
      in place of the caller's projects.

    Pagination: no supported paging parameters.

    Args:
        test_execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):
        trace_id (UUID | Unset):
        traceId (UUID | Unset):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse
    """

    return sync_detailed(
        client=client,
        test_execution_id=test_execution_id,
        call_execution_id=call_execution_id,
        trace_id=trace_id,
        traceId=traceId,
        project_id=project_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    test_execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    traceId: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
) -> Response[
    ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse
]:
    """Return the heavy / detail-only fields for a single voice call.

     Query params:
    - trace_id or legacy traceId (required) — UUID of the voice call trace.
    - project_id (optional) — the project the call was opened from.
    - test_execution_id or call_execution_id (optional) — a run the caller
      can read; the hidden simulation project of that run's agent is read
      in place of the caller's projects.

    Pagination: no supported paging parameters.

    Args:
        test_execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):
        trace_id (UUID | Unset):
        traceId (UUID | Unset):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        call_execution_id=call_execution_id,
        trace_id=trace_id,
        traceId=traceId,
        project_id=project_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    test_execution_id: UUID | Unset = UNSET,
    call_execution_id: UUID | Unset = UNSET,
    trace_id: UUID | Unset = UNSET,
    traceId: UUID | Unset = UNSET,
    project_id: UUID | Unset = UNSET,
) -> (
    ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse | None
):
    """Return the heavy / detail-only fields for a single voice call.

     Query params:
    - trace_id or legacy traceId (required) — UUID of the voice call trace.
    - project_id (optional) — the project the call was opened from.
    - test_execution_id or call_execution_id (optional) — a run the caller
      can read; the hidden simulation project of that run's agent is read
      in place of the caller's projects.

    Pagination: no supported paging parameters.

    Args:
        test_execution_id (UUID | Unset):
        call_execution_id (UUID | Unset):
        trace_id (UUID | Unset):
        traceId (UUID | Unset):
        project_id (UUID | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorResponse | ManagementAPIErrorResponse | TraceVoiceCallDetailResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            test_execution_id=test_execution_id,
            call_execution_id=call_execution_id,
            trace_id=trace_id,
            traceId=traceId,
            project_id=project_id,
        )
    ).parsed
