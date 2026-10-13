from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.external_run_results_request import ExternalRunResultsRequest
from ...models.external_run_results_response import ExternalRunResultsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import Response


def _get_kwargs(
    run_id: str,
    *,
    body: ExternalRunResultsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/experiment-runs/{run_id}/results/".format(
            run_id=quote(str(run_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = ExternalRunResultsResponse.from_dict(response.json())

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
    ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExternalRunResultsRequest,
) -> Response[
    ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Atomically ingest 1–100 caller-executed results for a pinned external run. Identical receipt/payload
    replay is a no-op, including after completion. Conflicts roll back the whole batch. Finalization is
    derived only when every planned identity is terminal. Body is limited to 2097152 bytes, each item to
    1048576 bytes and each output/error/usage JSON field to 262144 bytes. This endpoint does not execute
    tasks or attest trace/evaluator provenance.

    Args:
        run_id (str):
        body (ExternalRunResultsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExternalRunResultsRequest,
) -> (
    ExternalRunResultsResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Atomically ingest 1–100 caller-executed results for a pinned external run. Identical receipt/payload
    replay is a no-op, including after completion. Conflicts roll back the whole batch. Finalization is
    derived only when every planned identity is terminal. Body is limited to 2097152 bytes, each item to
    1048576 bytes and each output/error/usage JSON field to 262144 bytes. This endpoint does not execute
    tasks or attest trace/evaluator provenance.

    Args:
        run_id (str):
        body (ExternalRunResultsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        run_id=run_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExternalRunResultsRequest,
) -> Response[
    ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """Atomically ingest 1–100 caller-executed results for a pinned external run. Identical receipt/payload
    replay is a no-op, including after completion. Conflicts roll back the whole batch. Finalization is
    derived only when every planned identity is terminal. Body is limited to 2097152 bytes, each item to
    1048576 bytes and each output/error/usage JSON field to 262144 bytes. This endpoint does not execute
    tasks or attest trace/evaluator provenance.

    Args:
        run_id (str):
        body (ExternalRunResultsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExternalRunResultsRequest,
) -> (
    ExternalRunResultsResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """Atomically ingest 1–100 caller-executed results for a pinned external run. Identical receipt/payload
    replay is a no-op, including after completion. Conflicts roll back the whole batch. Finalization is
    derived only when every planned identity is terminal. Body is limited to 2097152 bytes, each item to
    1048576 bytes and each output/error/usage JSON field to 262144 bytes. This endpoint does not execute
    tasks or attest trace/evaluator provenance.

    Args:
        run_id (str):
        body (ExternalRunResultsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExternalRunResultsResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            client=client,
            body=body,
        )
    ).parsed
