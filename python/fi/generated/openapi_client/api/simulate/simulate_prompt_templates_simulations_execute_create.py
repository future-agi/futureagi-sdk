from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.execute_prompt_simulation_request import ExecutePromptSimulationRequest
from ...models.execute_prompt_simulation_response import ExecutePromptSimulationResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...types import Response


def _get_kwargs(
    prompt_template_id: str,
    run_test_id: str,
    *,
    body: ExecutePromptSimulationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/prompt-templates/{prompt_template_id}/simulations/{run_test_id}/execute/".format(
            prompt_template_id=quote(str(prompt_template_id), safe=""),
            run_test_id=quote(str(run_test_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
):
    if response.status_code == 200:
        response_200 = ExecutePromptSimulationResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ApiTextErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[
    ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
]:
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
    body: ExecutePromptSimulationRequest,
) -> Response[
    ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
]:
    """Execute a prompt-based simulation run.

     Request Body (optional):
    - scenario_ids: List of specific scenario IDs to run (default: all scenarios)
    - select_all: If true, run all scenarios except ones in scenario_ids

    Args:
        prompt_template_id (str):
        run_test_id (str):
        body (ExecutePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
        body=body,
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
    body: ExecutePromptSimulationRequest,
) -> (
    ApiTextErrorResponse
    | ExecutePromptSimulationResponse
    | ManagementAPIErrorResponse
    | None
):
    """Execute a prompt-based simulation run.

     Request Body (optional):
    - scenario_ids: List of specific scenario IDs to run (default: all scenarios)
    - select_all: If true, run all scenarios except ones in scenario_ids

    Args:
        prompt_template_id (str):
        run_test_id (str):
        body (ExecutePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
    """

    return sync_detailed(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecutePromptSimulationRequest,
) -> Response[
    ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
]:
    """Execute a prompt-based simulation run.

     Request Body (optional):
    - scenario_ids: List of specific scenario IDs to run (default: all scenarios)
    - select_all: If true, run all scenarios except ones in scenario_ids

    Args:
        prompt_template_id (str):
        run_test_id (str):
        body (ExecutePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        run_test_id=run_test_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    prompt_template_id: str,
    run_test_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecutePromptSimulationRequest,
) -> (
    ApiTextErrorResponse
    | ExecutePromptSimulationResponse
    | ManagementAPIErrorResponse
    | None
):
    """Execute a prompt-based simulation run.

     Request Body (optional):
    - scenario_ids: List of specific scenario IDs to run (default: all scenarios)
    - select_all: If true, run all scenarios except ones in scenario_ids

    Args:
        prompt_template_id (str):
        run_test_id (str):
        body (ExecutePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ExecutePromptSimulationResponse | ManagementAPIErrorResponse
    """

    return (
        await asyncio_detailed(
            prompt_template_id=prompt_template_id,
            run_test_id=run_test_id,
            client=client,
            body=body,
        )
    ).parsed
