from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.eval_list_response import EvalListResponse
from ...models.management_api_error_response import ManagementAPIErrorResponse
from ...models.model_hub_error_response import ModelHubErrorResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    dataset_id: str,
    *,
    eval_type: str | Unset = UNSET,
    search_text: str | Unset = UNSET,
    eval_categories: str | Unset = UNSET,
    eval_tags: list[str] | Unset = UNSET,
    use_cases: list[str] | Unset = UNSET,
    experiment_id: UUID | Unset = UNSET,
    order: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["eval_type"] = eval_type

    params["search_text"] = search_text

    params["eval_categories"] = eval_categories

    json_eval_tags: list[str] | Unset = UNSET
    if not isinstance(eval_tags, Unset):
        json_eval_tags = eval_tags

    params["eval_tags"] = json_eval_tags

    json_use_cases: list[str] | Unset = UNSET
    if not isinstance(use_cases, Unset):
        json_use_cases = use_cases

    params["use_cases"] = json_use_cases

    json_experiment_id: str | Unset = UNSET
    if not isinstance(experiment_id, Unset):
        json_experiment_id = str(experiment_id)
    params["experiment_id"] = json_experiment_id

    params["order"] = order

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/model-hub/develops/{dataset_id}/get_evals_list/".format(
            dataset_id=quote(str(dataset_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse:
    if response.status_code == 200:
        response_200 = EvalListResponse.from_dict(response.json())

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
) -> Response[EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: str | Unset = UNSET,
    search_text: str | Unset = UNSET,
    eval_categories: str | Unset = UNSET,
    eval_tags: list[str] | Unset = UNSET,
    use_cases: list[str] | Unset = UNSET,
    experiment_id: UUID | Unset = UNSET,
    order: str | Unset = UNSET,
) -> Response[EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    """
    Args:
        dataset_id (str):
        eval_type (str | Unset):
        search_text (str | Unset):
        eval_categories (str | Unset):
        eval_tags (list[str] | Unset):
        use_cases (list[str] | Unset):
        experiment_id (UUID | Unset):
        order (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_type=eval_type,
        search_text=search_text,
        eval_categories=eval_categories,
        eval_tags=eval_tags,
        use_cases=use_cases,
        experiment_id=experiment_id,
        order=order,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: str | Unset = UNSET,
    search_text: str | Unset = UNSET,
    eval_categories: str | Unset = UNSET,
    eval_tags: list[str] | Unset = UNSET,
    use_cases: list[str] | Unset = UNSET,
    experiment_id: UUID | Unset = UNSET,
    order: str | Unset = UNSET,
) -> EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        eval_type (str | Unset):
        search_text (str | Unset):
        eval_categories (str | Unset):
        eval_tags (list[str] | Unset):
        use_cases (list[str] | Unset):
        experiment_id (UUID | Unset):
        order (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return sync_detailed(
        dataset_id=dataset_id,
        client=client,
        eval_type=eval_type,
        search_text=search_text,
        eval_categories=eval_categories,
        eval_tags=eval_tags,
        use_cases=use_cases,
        experiment_id=experiment_id,
        order=order,
    ).parsed


async def asyncio_detailed(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: str | Unset = UNSET,
    search_text: str | Unset = UNSET,
    eval_categories: str | Unset = UNSET,
    eval_tags: list[str] | Unset = UNSET,
    use_cases: list[str] | Unset = UNSET,
    experiment_id: UUID | Unset = UNSET,
    order: str | Unset = UNSET,
) -> Response[EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]:
    """
    Args:
        dataset_id (str):
        eval_type (str | Unset):
        search_text (str | Unset):
        eval_categories (str | Unset):
        eval_tags (list[str] | Unset):
        use_cases (list[str] | Unset):
        experiment_id (UUID | Unset):
        order (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse]
    """

    kwargs = _get_kwargs(
        dataset_id=dataset_id,
        eval_type=eval_type,
        search_text=search_text,
        eval_categories=eval_categories,
        eval_tags=eval_tags,
        use_cases=use_cases,
        experiment_id=experiment_id,
        order=order,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    dataset_id: str,
    *,
    client: AuthenticatedClient | Client,
    eval_type: str | Unset = UNSET,
    search_text: str | Unset = UNSET,
    eval_categories: str | Unset = UNSET,
    eval_tags: list[str] | Unset = UNSET,
    use_cases: list[str] | Unset = UNSET,
    experiment_id: UUID | Unset = UNSET,
    order: str | Unset = UNSET,
) -> EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse | None:
    """
    Args:
        dataset_id (str):
        eval_type (str | Unset):
        search_text (str | Unset):
        eval_categories (str | Unset):
        eval_tags (list[str] | Unset):
        use_cases (list[str] | Unset):
        experiment_id (UUID | Unset):
        order (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EvalListResponse | ManagementAPIErrorResponse | ModelHubErrorResponse
    """

    return (
        await asyncio_detailed(
            dataset_id=dataset_id,
            client=client,
            eval_type=eval_type,
            search_text=search_text,
            eval_categories=eval_categories,
            eval_tags=eval_tags,
            use_cases=use_cases,
            experiment_id=experiment_id,
            order=order,
        )
    ).parsed
