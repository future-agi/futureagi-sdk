from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_error_response import EvalErrorResponse
from ...models.eval_summary_response import EvalSummaryResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    agent_id: str,
    version_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/simulate/agent-definitions/{agent_id}/versions/{version_id}/eval-summary/".format(
            agent_id=quote(str(agent_id), safe=""),
            version_id=quote(str(version_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = EvalSummaryResponse.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = EvalErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = EvalErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]:
    """Get the eval summary of an agent version.

    Args:
        agent_id (str):
        version_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        version_id=version_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse | None:
    """Get the eval summary of an agent version.

    Args:
        agent_id (str):
        version_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        agent_id=agent_id,
        version_id=version_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]:
    """Get the eval summary of an agent version.

    Args:
        agent_id (str):
        version_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        agent_id=agent_id,
        version_id=version_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    agent_id: str,
    version_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse | None:
    """Get the eval summary of an agent version.

    Args:
        agent_id (str):
        version_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalErrorResponse | EvalSummaryResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            agent_id=agent_id,
            version_id=version_id,
            client=client,
        )
    ).parsed
