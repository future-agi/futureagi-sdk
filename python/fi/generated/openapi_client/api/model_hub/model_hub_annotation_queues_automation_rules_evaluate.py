from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.automation_rule_evaluate_accepted_response import (
    AutomationRuleEvaluateAcceptedResponse,
)
from ...models.automation_rule_evaluate_response import AutomationRuleEvaluateResponse
from ...models.empty_request import EmptyRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    queue_id: str,
    id: UUID,
    *,
    body: EmptyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/annotation-queues/{queue_id}/automation-rules/{id}/evaluate/".format(
            queue_id=quote(str(queue_id), safe=""),
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
):
    if response.status_code == 200:
        response_200 = AutomationRuleEvaluateResponse.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = AutomationRuleEvaluateAcceptedResponse.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ApiTextErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ApiTextErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
]:
    """Trigger a manual rule run with a sync-or-async branch.

     Small runs (filter resolves to ≤ ``RULE_RUN_SYNC_THRESHOLD``) finish
    in the HTTP request and return 200 with the result — fast feedback
    for the common case. Large runs (mostly first-ever runs on backlogs
    or rules with wide filters) hand the work to a Temporal activity and
    return 202 immediately. The activity emails creator + queue managers
    on completion.

    The peek is a cheap dry-run (``[:cap+1]`` LIMIT, no COUNT(*)) — sub-
    100ms even on 10M+ row trace tables — so this branch costs little
    even when it ends up taking the sync path.

    Args:
        queue_id (str):
        id (UUID):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | AutomationRuleEvaluateAcceptedResponse | AutomationRuleEvaluateResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
    | None
):
    """Trigger a manual rule run with a sync-or-async branch.

     Small runs (filter resolves to ≤ ``RULE_RUN_SYNC_THRESHOLD``) finish
    in the HTTP request and return 200 with the result — fast feedback
    for the common case. Large runs (mostly first-ever runs on backlogs
    or rules with wide filters) hand the work to a Temporal activity and
    return 202 immediately. The activity emails creator + queue managers
    on completion.

    The peek is a cheap dry-run (``[:cap+1]`` LIMIT, no COUNT(*)) — sub-
    100ms even on 10M+ row trace tables — so this branch costs little
    even when it ends up taking the sync path.

    Args:
        queue_id (str):
        id (UUID):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | AutomationRuleEvaluateAcceptedResponse | AutomationRuleEvaluateResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        queue_id=queue_id,
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> Response[
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
]:
    """Trigger a manual rule run with a sync-or-async branch.

     Small runs (filter resolves to ≤ ``RULE_RUN_SYNC_THRESHOLD``) finish
    in the HTTP request and return 200 with the result — fast feedback
    for the common case. Large runs (mostly first-ever runs on backlogs
    or rules with wide filters) hand the work to a Temporal activity and
    return 202 immediately. The activity emails creator + queue managers
    on completion.

    The peek is a cheap dry-run (``[:cap+1]`` LIMIT, no COUNT(*)) — sub-
    100ms even on 10M+ row trace tables — so this branch costs little
    even when it ends up taking the sync path.

    Args:
        queue_id (str):
        id (UUID):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | AutomationRuleEvaluateAcceptedResponse | AutomationRuleEvaluateResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        queue_id=queue_id,
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    queue_id: str,
    id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: EmptyRequest,
) -> (
    ApiTextErrorResponse
    | AutomationRuleEvaluateAcceptedResponse
    | AutomationRuleEvaluateResponse
    | ManagementAPIErrorResponse
    | None
):
    """Trigger a manual rule run with a sync-or-async branch.

     Small runs (filter resolves to ≤ ``RULE_RUN_SYNC_THRESHOLD``) finish
    in the HTTP request and return 200 with the result — fast feedback
    for the common case. Large runs (mostly first-ever runs on backlogs
    or rules with wide filters) hand the work to a Temporal activity and
    return 202 immediately. The activity emails creator + queue managers
    on completion.

    The peek is a cheap dry-run (``[:cap+1]`` LIMIT, no COUNT(*)) — sub-
    100ms even on 10M+ row trace tables — so this branch costs little
    even when it ends up taking the sync path.

    Args:
        queue_id (str):
        id (UUID):
        body (EmptyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | AutomationRuleEvaluateAcceptedResponse | AutomationRuleEvaluateResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            queue_id=queue_id,
            id=id,
            client=client,
            body=body,
        )
    ).parsed
