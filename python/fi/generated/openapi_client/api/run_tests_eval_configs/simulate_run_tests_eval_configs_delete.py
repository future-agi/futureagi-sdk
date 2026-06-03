from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.delete_eval_config_response import DeleteEvalConfigResponse
from ...models.eval_error_response import EvalErrorResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    run_test_id: str,
    eval_config_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/simulate/run-tests/{run_test_id}/eval-configs/{eval_config_id}/".format(
            run_test_id=quote(str(run_test_id), safe=""),
            eval_config_id=quote(str(eval_config_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse:
    if response.status_code == 200:
        response_200 = DeleteEvalConfigResponse.from_dict(response.json())

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
    Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse
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
) -> Response[
    Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse
]:
    """Delete evaluation configuration

     Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

    Args:
        run_test_id (str):
        eval_config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
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
) -> (
    Any
    | DeleteEvalConfigResponse
    | EvalErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Delete evaluation configuration

     Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

    Args:
        run_test_id (str):
        eval_config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse
]:
    """Delete evaluation configuration

     Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

    Args:
        run_test_id (str):
        eval_config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        run_test_id=run_test_id,
        eval_config_id=eval_config_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_test_id: str,
    eval_config_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteEvalConfigResponse
    | EvalErrorResponse
    | ManagementAPIErrorResponse
    | None
):
    """Delete evaluation configuration

     Soft-deletes an evaluation configuration. Cannot delete the last remaining config in the test run.

    Args:
        run_test_id (str):
        eval_config_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteEvalConfigResponse | EvalErrorResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            run_test_id=run_test_id,
            eval_config_id=eval_config_id,
            client=client,
        )
    ).parsed
