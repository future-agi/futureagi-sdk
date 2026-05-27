from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_structure_response import EvalStructureResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_develops_get_eval_structure_read_eval_type import (
    ModelHubDevelopsGetEvalStructureReadEvalType,
)
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import UNSET, Response


def _get_kwargs(
    dataset_id: str,
    eval_id: str,
    *,
    eval_type: ModelHubDevelopsGetEvalStructureReadEvalType,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_eval_type = eval_type.value
    params["eval_type"] = json_eval_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/develops/{dataset_id}/get_eval_structure/{eval_id}/".format(
            dataset_id=quote(str(dataset_id), safe=""),
            eval_id=quote(str(eval_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = EvalStructureResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ModelHubErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = ModelHubErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ModelHubErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = ModelHubErrorResponse.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = ModelHubErrorResponse.from_dict(response.json())

        return response_500

    response_default = ManagementAPIErrorResponse.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: ModelHubDevelopsGetEvalStructureReadEvalType,
) -> Response[
    EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        dataset_id (str):
        eval_id (str):
        eval_type (ModelHubDevelopsGetEvalStructureReadEvalType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_id=eval_id,
        eval_type=eval_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: ModelHubDevelopsGetEvalStructureReadEvalType,
) -> EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        eval_id (str):
        eval_type (ModelHubDevelopsGetEvalStructureReadEvalType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        eval_id=eval_id,
        client=client,
        eval_type=eval_type,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: ModelHubDevelopsGetEvalStructureReadEvalType,
) -> Response[
    EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """
    Args:
        dataset_id (str):
        eval_id (str):
        eval_type (ModelHubDevelopsGetEvalStructureReadEvalType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_id=eval_id,
        eval_type=eval_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: ModelHubDevelopsGetEvalStructureReadEvalType,
) -> EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        eval_id (str):
        eval_type (ModelHubDevelopsGetEvalStructureReadEvalType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalStructureResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            eval_id=eval_id,
            client=client,
            eval_type=eval_type,
        )
    ).parsed
