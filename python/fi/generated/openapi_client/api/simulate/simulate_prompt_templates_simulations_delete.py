from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    prompt_template_id: str,
    run_test_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/".format(
            prompt_template_id=quote(str(prompt_template_id), safe=""),
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ApiTextErrorResponse | ManagementAPIErrorResponse:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 404:
        response_404 = ApiTextErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ApiTextErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ApiTextErrorResponse | ManagementAPIErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ApiTextErrorResponse | ManagementAPIErrorResponse]:
    """Soft delete a prompt simulation run.

    Args:
        prompt_template_id (str):
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ApiTextErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ApiTextErrorResponse | ManagementAPIErrorResponse | None:
    """Soft delete a prompt simulation run.

    Args:
        prompt_template_id (str):
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ApiTextErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ApiTextErrorResponse | ManagementAPIErrorResponse]:
    """Soft delete a prompt simulation run.

    Args:
        prompt_template_id (str):
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ApiTextErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ApiTextErrorResponse | ManagementAPIErrorResponse | None:
    """Soft delete a prompt simulation run.

    Args:
        prompt_template_id (str):
        run_test_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ApiTextErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            prompt_template_id=prompt_template_id,
            run_test_id=run_test_id,
            client=client,
        )
    ).parsed
