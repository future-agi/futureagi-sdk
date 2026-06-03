from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_error_with_details_response import ApiErrorWithDetailsResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.persona_create import PersonaCreate
from ...types import Response


def _get_kwargs(
    *,
    body: PersonaCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/api/personas/",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate:
    if response.status_code == 201:
        response_201 = PersonaCreate.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = ApiErrorWithDetailsResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PersonaCreate,
) -> Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate]:
    """Create a new workspace-level persona

    Args:
        body (PersonaCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PersonaCreate,
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate | None:
    """Create a new workspace-level persona

    Args:
        body (PersonaCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PersonaCreate,
) -> Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate]:
    """Create a new workspace-level persona

    Args:
        body (PersonaCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PersonaCreate,
) -> ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate | None:
    """Create a new workspace-level persona

    Args:
        body (PersonaCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiErrorWithDetailsResponse | ManagementAPIErrorResponse | PersonaCreate
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
