from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...models.sdk_standalone_eval_v2_response import SDKStandaloneEvalV2Response
from ...types import UNSET, Response


def _get_kwargs(
    *,
    eval_id: UUID,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_eval_id = str(eval_id)
    params["eval_id"] = json_eval_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sdk/api/v1/new-eval/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response:
    if response.status_code == 200:
        response_200 = SDKStandaloneEvalV2Response.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = SDKErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = SDKErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response
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
    eval_id: UUID,
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response
]:
    """
    Args:
        eval_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response]
    """

    kwargs = _get_kwargs(
        eval_id=eval_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    eval_id: UUID,
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response | None:
    """
    Args:
        eval_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response
    """

    return sync_detailed(
        client=client,
        eval_id=eval_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    eval_id: UUID,
) -> Response[
    ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response
]:
    """
    Args:
        eval_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response]
    """

    kwargs = _get_kwargs(
        eval_id=eval_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    eval_id: UUID,
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response | None:
    """
    Args:
        eval_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKStandaloneEvalV2Response
    """

    return (
        await asyncio_detailed(
            client=client,
            eval_id=eval_id,
        )
    ).parsed
