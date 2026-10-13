from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.persona_duplicate_request import PersonaDuplicateRequest
from ...models.persona_duplicate_response import PersonaDuplicateResponse
from ...types import Response


def _get_kwargs(
    persona_id: str,
    *,
    body: PersonaDuplicateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/api/personas/duplicate/{persona_id}/".format(
            persona_id=quote(str(persona_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse:
    if response.status_code == 201:
        response_201 = PersonaDuplicateResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    persona_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    """Duplicate a persona by ID

    Args:
        persona_id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse]
    """

    kwargs = _get_kwargs(
        persona_id=persona_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    persona_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> (
    ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse | None
):
    """Duplicate a persona by ID

    Args:
        persona_id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
    """

    return sync_detailed(
        persona_id=persona_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    persona_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
]:
    """Duplicate a persona by ID

    Args:
        persona_id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse]
    """

    kwargs = _get_kwargs(
        persona_id=persona_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    persona_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonaDuplicateRequest,
) -> (
    ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse | None
):
    """Duplicate a persona by ID

    Args:
        persona_id (str):
        body (PersonaDuplicateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PersonaDuplicateResponse
    """

    return (
        await asyncio_detailed(
            persona_id=persona_id,
            client=client,
            body=body,
        )
    ).parsed
