from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.sdk_error_response import SDKErrorResponse
from ...models.sdk_eval_template_response import SDKEvalTemplateResponse
from ...types import Response


def _get_kwargs(
    eval_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sdk/api/v1/eval/{eval_id}/".format(
            eval_id=quote(str(eval_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse:
    if response.status_code == 200:
        response_200 = SDKEvalTemplateResponse.from_dict(response.json())

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
) -> Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse]:
    """
    Args:
        eval_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse]
    """

    kwargs = _get_kwargs(
        eval_id=eval_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse | None:
    """
    Args:
        eval_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse
    """

    return sync_detailed(
        eval_id=eval_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse]:
    """
    Args:
        eval_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse]
    """

    kwargs = _get_kwargs(
        eval_id=eval_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse | None:
    """
    Args:
        eval_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManagementAPIErrorResponse | SDKErrorResponse | SDKEvalTemplateResponse
    """

    return (
        await asyncio_detailed(
            eval_id=eval_id,
            client=client,
        )
    ).parsed
