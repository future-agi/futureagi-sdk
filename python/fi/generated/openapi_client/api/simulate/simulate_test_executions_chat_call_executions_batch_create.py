from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.empty_request import EmptyRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.test_execution_chat_batch_response import TestExecutionChatBatchResponse
from ...types import Response


def _get_kwargs(
    test_execution_id: str,
    *,
    body: EmptyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/test-executions/{test_execution_id}/chat/call-executions/batch/".format(
            test_execution_id=quote(str(test_execution_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse:
    if response.status_code == 200:
        response_200 = TestExecutionChatBatchResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse
]:
    """Create a batch of CallExecution records for chat execution (exactly 10 per API call).

     This follows the same flow as inbound/outbound calls:
    1. Resolve SimulatorAgent (scenario > run_test > fallback)
    2. Extract base_prompt from SimulatorAgent
    3. Handle dataset scenarios (create one CallExecution per row)
    4. Enhance prompt with row data if applicable
    5. Store proper metadata in CallExecution

    Returns exactly 10 CallExecution objects per API call.
    hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionChatBatchResponse
    | None
):
    """Create a batch of CallExecution records for chat execution (exactly 10 per API call).

     This follows the same flow as inbound/outbound calls:
    1. Resolve SimulatorAgent (scenario > run_test > fallback)
    2. Extract base_prompt from SimulatorAgent
    3. Handle dataset scenarios (create one CallExecution per row)
    4. Enhance prompt with row data if applicable
    5. Store proper metadata in CallExecution

    Returns exactly 10 CallExecution objects per API call.
    hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse
    """

    return sync_detailed(
        test_execution_id=test_execution_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse
]:
    """Create a batch of CallExecution records for chat execution (exactly 10 per API call).

     This follows the same flow as inbound/outbound calls:
    1. Resolve SimulatorAgent (scenario > run_test > fallback)
    2. Extract base_prompt from SimulatorAgent
    3. Handle dataset scenarios (create one CallExecution per row)
    4. Enhance prompt with row data if applicable
    5. Store proper metadata in CallExecution

    Returns exactly 10 CallExecution objects per API call.
    hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse]
    """

    kwargs = _get_kwargs(
        test_execution_id=test_execution_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    test_execution_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | TestExecutionChatBatchResponse
    | None
):
    """Create a batch of CallExecution records for chat execution (exactly 10 per API call).

     This follows the same flow as inbound/outbound calls:
    1. Resolve SimulatorAgent (scenario > run_test > fallback)
    2. Extract base_prompt from SimulatorAgent
    3. Handle dataset scenarios (create one CallExecution per row)
    4. Enhance prompt with row data if applicable
    5. Store proper metadata in CallExecution

    Returns exactly 10 CallExecution objects per API call.
    hasMore is true until ALL row_ids of ALL scenarios have CallExecution objects created.

    Args:
        test_execution_id (str):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | TestExecutionChatBatchResponse
    """

    return (
        await asyncio_detailed(
            test_execution_id=test_execution_id,
            client=client,
            body=body,
        )
    ).parsed
