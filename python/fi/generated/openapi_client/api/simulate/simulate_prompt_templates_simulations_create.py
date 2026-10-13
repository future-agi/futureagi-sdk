from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_text_error_response import ApiTextErrorResponse
from ...models.create_prompt_simulation_request import CreatePromptSimulationRequest
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.prompt_simulation_run_response import PromptSimulationRunResponse
from ...types import Response


def _get_kwargs(
    prompt_template_id: str,
    *,
    body: CreatePromptSimulationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/simulate/prompt-templates/{prompt_template_id}/simulations/".format(
            prompt_template_id=quote(str(prompt_template_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse:
    if response.status_code == 201:
        response_201 = PromptSimulationRunResponse.from_dict(response.json())

        return response_201

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
    ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    prompt_template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreatePromptSimulationRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse
]:
    """Create a new prompt-based simulation run.

     Request Body:
    - name: Name of the simulation run
    - description: Optional description
    - prompt_version_id: The prompt version to use
    - scenario_ids: List of scenario IDs to run
    - dataset_row_ids: Optional list of specific row IDs
    - evaluations_config: Optional evaluation configurations
    - enable_tool_evaluation: Optional boolean to enable tool evaluation

    Args:
        prompt_template_id (str):
        body (CreatePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    prompt_template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreatePromptSimulationRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationRunResponse
    | None
):
    """Create a new prompt-based simulation run.

     Request Body:
    - name: Name of the simulation run
    - description: Optional description
    - prompt_version_id: The prompt version to use
    - scenario_ids: List of scenario IDs to run
    - dataset_row_ids: Optional list of specific row IDs
    - evaluations_config: Optional evaluation configurations
    - enable_tool_evaluation: Optional boolean to enable tool evaluation

    Args:
        prompt_template_id (str):
        body (CreatePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse
    """

    return sync_detailed(
        prompt_template_id=prompt_template_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    prompt_template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreatePromptSimulationRequest,
) -> Response[
    ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse
]:
    """Create a new prompt-based simulation run.

     Request Body:
    - name: Name of the simulation run
    - description: Optional description
    - prompt_version_id: The prompt version to use
    - scenario_ids: List of scenario IDs to run
    - dataset_row_ids: Optional list of specific row IDs
    - evaluations_config: Optional evaluation configurations
    - enable_tool_evaluation: Optional boolean to enable tool evaluation

    Args:
        prompt_template_id (str):
        body (CreatePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse]
    """

    kwargs = _get_kwargs(
        prompt_template_id=prompt_template_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    prompt_template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreatePromptSimulationRequest,
) -> (
    ApiTextErrorResponse
    | ManagementAPIErrorResponse
    | PromptSimulationRunResponse
    | None
):
    """Create a new prompt-based simulation run.

     Request Body:
    - name: Name of the simulation run
    - description: Optional description
    - prompt_version_id: The prompt version to use
    - scenario_ids: List of scenario IDs to run
    - dataset_row_ids: Optional list of specific row IDs
    - evaluations_config: Optional evaluation configurations
    - enable_tool_evaluation: Optional boolean to enable tool evaluation

    Args:
        prompt_template_id (str):
        body (CreatePromptSimulationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiTextErrorResponse | ManagementAPIErrorResponse | PromptSimulationRunResponse
    """

    return (
        await asyncio_detailed(
            prompt_template_id=prompt_template_id,
            client=client,
            body=body,
        )
    ).parsed
