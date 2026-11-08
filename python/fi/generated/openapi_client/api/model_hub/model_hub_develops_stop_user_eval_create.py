from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.develop_dataset_message_response import DevelopDatasetMessageResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...models.stop_user_eval_request import StopUserEvalRequest
from ...types import Response


def _get_kwargs(
    dataset_id: str,
    eval_id: str,
    *,
    body: StopUserEvalRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/model-hub/develops/{dataset_id}/stop_user_eval/{eval_id}/".format(
            dataset_id=quote(str(dataset_id), safe=""),
            eval_id=quote(str(eval_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = DevelopDatasetMessageResponse.from_dict(response.json())

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
    DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
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
    body: StopUserEvalRequest,
) -> Response[
    DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """POST /develops/<dataset_id>/stop_user_eval/<eval_id>/
    Stops a running evaluation by setting its status to Completed.

     Accepts optional experiment_id in the body. When present, the eval is
    looked up via source_id=experiment_id (experiment-scoped UserEvalMetric)
    and cells are updated across both base columns (source_id=eval_id) and
    per-EDT columns (source_id ending with `-sourceid-{eval_id}`).

    Args:
        dataset_id (str):
        eval_id (str):
        body (StopUserEvalRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_id=eval_id,
        body=body,
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
    body: StopUserEvalRequest,
) -> (
    DevelopDatasetMessageResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """POST /develops/<dataset_id>/stop_user_eval/<eval_id>/
    Stops a running evaluation by setting its status to Completed.

     Accepts optional experiment_id in the body. When present, the eval is
    looked up via source_id=experiment_id (experiment-scoped UserEvalMetric)
    and cells are updated across both base columns (source_id=eval_id) and
    per-EDT columns (source_id ending with `-sourceid-{eval_id}`).

    Args:
        dataset_id (str):
        eval_id (str):
        body (StopUserEvalRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        eval_id=eval_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: StopUserEvalRequest,
) -> Response[
    DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
]:
    """POST /develops/<dataset_id>/stop_user_eval/<eval_id>/
    Stops a running evaluation by setting its status to Completed.

     Accepts optional experiment_id in the body. When present, the eval is
    looked up via source_id=experiment_id (experiment-scoped UserEvalMetric)
    and cells are updated across both base columns (source_id=eval_id) and
    per-EDT columns (source_id ending with `-sourceid-{eval_id}`).

    Args:
        dataset_id (str):
        eval_id (str):
        body (StopUserEvalRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_id=eval_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    eval_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: StopUserEvalRequest,
) -> (
    DevelopDatasetMessageResponse
    | ManagementAPIErrorResponse
    | ModelHubErrorResponse
    | None
):
    """POST /develops/<dataset_id>/stop_user_eval/<eval_id>/
    Stops a running evaluation by setting its status to Completed.

     Accepts optional experiment_id in the body. When present, the eval is
    looked up via source_id=experiment_id (experiment-scoped UserEvalMetric)
    and cells are updated across both base columns (source_id=eval_id) and
    per-EDT columns (source_id ending with `-sourceid-{eval_id}`).

    Args:
        dataset_id (str):
        eval_id (str):
        body (StopUserEvalRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DevelopDatasetMessageResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            eval_id=eval_id,
            client=client,
            body=body,
        )
    ).parsed
