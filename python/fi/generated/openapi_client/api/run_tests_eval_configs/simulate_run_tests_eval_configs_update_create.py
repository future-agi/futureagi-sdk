from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_config_update_request import EvalConfigUpdateRequest
from ...models.eval_config_update_response import EvalConfigUpdateResponse
from ...models.eval_error_response import EvalErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    run_test_id: str,
    eval_config_id: str,
    *,
    body: EvalConfigUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/update/".format(
            run_test_id=quote(str(run_test_id), safe=""),
            eval_config_id=quote(str(eval_config_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = EvalConfigUpdateResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = EvalErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

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
) -> Response[
    Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EvalConfigUpdateRequest,
) -> Response[
    Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse
]:
    """Update evaluation configuration

     Updates an evaluation configuration and optionally triggers a rerun. When run=true,
    test_execution_id is required.

    Args:
        run_test_id (str):
        eval_config_id (str):
        body (EvalConfigUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EvalConfigUpdateRequest,
) -> (
    Any
    | EvalConfigUpdateResponse
    | EvalErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Update evaluation configuration

     Updates an evaluation configuration and optionally triggers a rerun. When run=true,
    test_execution_id is required.

    Args:
        run_test_id (str):
        eval_config_id (str):
        body (EvalConfigUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EvalConfigUpdateRequest,
) -> Response[
    Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse
]:
    """Update evaluation configuration

     Updates an evaluation configuration and optionally triggers a rerun. When run=true,
    test_execution_id is required.

    Args:
        run_test_id (str):
        eval_config_id (str):
        body (EvalConfigUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EvalConfigUpdateRequest,
) -> (
    Any
    | EvalConfigUpdateResponse
    | EvalErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Update evaluation configuration

     Updates an evaluation configuration and optionally triggers a rerun. When run=true,
    test_execution_id is required.

    Args:
        run_test_id (str):
        eval_config_id (str):
        body (EvalConfigUpdateRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | EvalConfigUpdateResponse | EvalErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            eval_config_id=eval_config_id,
            client=client,
            body=body,
        )
    ).parsed
