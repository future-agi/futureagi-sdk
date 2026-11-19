"""``AsyncFutureAGIClient``: the async twin of :class:`fi.FutureAGIClient`.

It drives the generated client's ``asyncio_detailed`` functions over one ``httpx.AsyncClient``
with the same defaults as the sync client: ``httpx.Timeout(30, connect=10)``, the retrying
transport (429 and pre-send connect errors any method; 502/503/504 idempotent methods only;
``Retry-After`` honoured; ``fi._http``) and keys resolved on the first request through
``fi._credentials``.

Today it covers what the experiments engine needs (``experiment_runs``) plus a raw request
helper; other groups move here as they are needed. The platform options, the lazily resolved
platform origin, typed errors and ``with_options`` are the sync client's.
"""

from __future__ import annotations

import copy
import dataclasses
import functools
import threading
from typing import Any, Mapping
from uuid import UUID

import httpx

from fi.tracing import AsyncTracingClient
from fi._core.core_http import check_redirect
from fi._credentials import Credentials, MissingAuthError
from fi._credentials import resolve as resolve_credentials
from fi._extra_headers import ExtraHeaders
from fi._http import ClientRetryingTransport, LazyKeyAuth
from fi.errors import api_error
from fi.knowledge_bases import AsyncKnowledgeBasesClient
from fi.prompts import AsyncPromptsClient
from fi.scores import AsyncScoresClient
from fi.futureagi_client import (
    FutureAGIAPIError,
    _adetailed,
    _as_timeout,
    _clean,
    _ClientOptions,
    _GeneratedClient,
    _typed_result,
    creds_missing,
)
from fi.generated.openapi_client.api.experiment_runs import (
    compare_experiment_runs,
    create_external_experiment_run,
    ingest_external_experiment_results,
)
from fi.generated.openapi_client.client import Client as GeneratedOpenAPIClient
from fi.generated.openapi_client.models.external_run_create_request import (
    ExternalRunCreateRequest,
)
from fi.generated.openapi_client.models.external_run_create_response import (
    ExternalRunCreateResponse,
)
from fi.generated.openapi_client.models.external_run_results_request import (
    ExternalRunResultsRequest,
)
from fi.generated.openapi_client.models.external_run_results_response import (
    ExternalRunResultsResponse,
)
from fi.generated.openapi_client.models.run_comparison_request import (
    RunComparisonRequest,
)
from fi.generated.openapi_client.models.run_comparison_response import (
    RunComparisonResponse,
)
from fi.generated.platform.catalog.models import AsyncModels
from fi.generated.platform.catalog.optimizations import AsyncOptimizations
from fi.generated.platform.catalog.workspaces import AsyncWorkspaces


class AsyncFutureAGIClient:
    """The async platform client.

    Simulation APIs are not offered in this release.
    """

    # FA catalog namespaces, bound in _build_namespaces by fi._core.catalog_registration.
    workspaces: AsyncWorkspaces
    optimizations: AsyncOptimizations
    models: AsyncModels
    tracing: AsyncTracingClient

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        base_url: str | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | httpx.Timeout | None = None,
        retries: int = 3,
        platform_base_url: str | None = None,
        workspace_id: str | None = None,
        organization_id: str | None = None,
        platform_token: str | None = None,
        allow_custom_platform_url: bool | None = None,
        allow_insecure_http: bool | None = None,
        extra_headers: Mapping[str, str] | str | None = None,
    ) -> None:
        """``extra_headers=`` adds headers to every request to ``base_url`` and wins over
        ``FI_EXTRA_HEADERS`` for the same name (``fi._extra_headers``: never the SDK's own auth headers,
        never another host). ``allow_insecure_http`` explicitly permits nonloopback HTTP for a
        platform Bearer token (else ``FI_ALLOW_INSECURE_HTTP``); False overrides the environment.
        Keys-mode HTTP warns about future refusal."""
        self.base_url = resolve_credentials(api_key, secret_key, base_url).base_url
        self._options = _ClientOptions(
            api_key,
            secret_key,
            dict(headers or {}),
            _as_timeout(timeout),
            retries,
            platform_base_url,
            workspace_id,
            organization_id,
            platform_token,
            allow_custom_platform_url,
            allow_insecure_http=allow_insecure_http,
        )
        self._extra_headers = ExtraHeaders(self.base_url, extra_headers)
        self._management_lock = threading.Lock()

        def _require() -> Credentials:
            creds = resolve_credentials(api_key, secret_key, self.base_url)
            if not creds.complete:
                raise MissingAuthError(
                    creds.api_key,
                    creds.secret_key,
                    cause=creds_missing(creds),
                    base_url=creds.base_url,
                    login_skipped=creds.login_skipped,
                )
            return creds

        self._auth = LazyKeyAuth(_require, extra=self._extra_headers)
        self._build_namespaces(ClientRetryingTransport(retries=retries), _as_timeout(timeout))

    def _build_namespaces(self, transport: ClientRetryingTransport, timeout: httpx.Timeout) -> None:
        self.generated_client: GeneratedOpenAPIClient = _GeneratedClient(
            base_url=self.base_url,
            headers=dict(self._options.headers),
            timeout=timeout,
            raise_on_unexpected_status=False,  # undeclared statuses are typed by _typed_result
            httpx_args={"auth": self._auth, "transport": transport},
        )
        from fi.environments import AsyncEnvironments
        self.__dict__.pop("agents", None)
        self.environments = AsyncEnvironments(self)
        self.knowledge_bases = AsyncKnowledgeBasesClient(self.generated_client)
        self.prompts = AsyncPromptsClient(self.generated_client)
        self.scores = AsyncScoresClient(self.generated_client)
        self.annotation_labels = self.scores.labels
        self.experiment_runs = AsyncExperimentRunsClient(self.generated_client)
        self.tracing = AsyncTracingClient(self)
        from fi._core.catalog_registration import register
        register(self, asynchronous=True)

    @property
    def connectors(self) -> Any:
        """Workspace MCP connections; OAuth completion remains in the browser."""
        from fi.connectors import AsyncConnectors
        return AsyncConnectors(self)

    @property
    def integrations(self) -> Any:
        """Data connections and their sync history."""
        from fi.integrations import AsyncIntegrations
        return AsyncIntegrations(self)

    @property
    def credentials(self) -> Any:
        """Workspace credential metadata, never credential mutations."""
        from fi.credentials import AsyncCredentials
        return AsyncCredentials(self)

    @functools.cached_property
    def agents(self) -> Any:
        """Managed agents and runs using this client's platform settings."""
        from fi.agents import AsyncAgents
        return AsyncAgents(self)

    @property
    def gateway(self) -> Any:
        """Async gateway management with personal platform credentials."""
        from fi.generated.platform.fa_management.gateway import AsyncGateway
        return AsyncGateway(self._management)

    @functools.cached_property
    def _management(self) -> Any:
        from fi._core.fa_registration import get_core
        return get_core(self, asynchronous=True)

    @functools.cached_property
    def _platform(self) -> Any:
        """The async platform executor (``fi._core.platform_base``), built on first use."""
        from fi._core.platform_async import AsyncPlatformCore
        from fi._core.transport import PlatformShared, Settings
        from fi._core.connector_policy import OPERATIONS as CONNECTOR_OPERATIONS

        return AsyncPlatformCore(PlatformShared(self._resolve_platform_origin, retries=self._options.retries,
                                                supplemental_table=CONNECTOR_OPERATIONS,
                                                extra_headers=self._extra_headers),
                                 Settings(timeout=self._options.timeout))

    def _resolve_platform_origin(self) -> Any:
        from fi._core.origins import resolve_platform

        o = self._options
        creds = resolve_credentials(
            o.api_key,
            o.secret_key,
            self.base_url,
            platform_base_url=o.platform_base_url,
            workspace_id=o.workspace_id,
            organization_id=o.organization_id,
            platform_token=o.platform_token,
        )
        from fi._credentials import CredentialsMissingError
        try:
            return resolve_platform(
                creds, allow_custom_platform_url=o.allow_custom_platform_url,
                allow_insecure_http=o.allow_insecure_http,
            )
        except CredentialsMissingError as error:
            raise MissingAuthError(
                creds.api_key, creds.secret_key, error,
                base_url=creds.base_url, login_skipped=creds.login_skipped,
            ) from error

    def with_options(self, *, timeout: float | httpx.Timeout | None = None, retries: int | None = None) -> "AsyncFutureAGIClient":
        """A copy with another default ``timeout`` and/or ``retries`` that shares this client's
        credentials and connection pools (closing the copy leaves the pools open)."""
        from fi._core.transport import shared_inner

        clone = copy.copy(self)
        clone.__dict__.pop("_platform", None)
        clone.__dict__["_management"] = self._management.with_settings(
            timeout=timeout, retries=retries
        )
        clone._options = dataclasses.replace(
            self._options,
            timeout=self._options.timeout if timeout is None else _as_timeout(timeout),
            retries=self._options.retries if retries is None else int(retries),
            copy=True,
        )
        inner, inner_async = shared_inner(self.generated_client._httpx_args["transport"])
        transport = ClientRetryingTransport(retries=clone._options.retries, wrapped=inner, wrapped_async=inner_async)
        clone._build_namespaces(transport, clone._options.timeout)
        clone.__dict__["_platform"] = self._platform.with_settings(timeout=timeout, retries=retries)
        return clone

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
    ) -> Any:
        kwargs: dict[str, Any] = {"method": method, "url": path, "params": _clean(query or {})}
        if body is not None:
            kwargs["json"] = body
        response = await self.generated_client.get_async_httpx_client().request(**kwargs)
        check_redirect(response, f"{method.upper()} {path}")
        payload: Any = None
        if response.content:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
        if response.status_code >= 400:
            raise api_error(int(response.status_code), payload, response.headers)
        return payload

    @property
    def auth(self) -> Credentials:
        """The SDK's own resolved keys and base URL (raises ``MissingAuthError`` when there are no
        keys); the same property as ``FutureAGIClient.auth``."""
        return self._auth.credentials

    async def aclose(self) -> None:
        await self.generated_client.get_async_httpx_client().aclose()
        for name in ("_platform", "_management"):
            if name in self.__dict__ and not self._options.copy:
                await self.__dict__[name].shared.aclose()

    async def __aenter__(self) -> "AsyncFutureAGIClient":
        await self.generated_client.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.generated_client.__aexit__(*args)
        for name in ("_platform", "_management"):
            if name in self.__dict__ and not self._options.copy:
                await self.__dict__[name].shared.aclose()


class AsyncExperimentRunsClient:
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        self._client = client

    async def create(self, body: ExternalRunCreateRequest) -> ExternalRunCreateResponse:
        response = await _adetailed(create_external_experiment_run.asyncio_detailed, client=self._client, body=body)
        return _typed_result(response, ExternalRunCreateResponse)

    async def ingest_results(
        self, run_id: str | UUID, body: ExternalRunResultsRequest
    ) -> ExternalRunResultsResponse:
        response = await _adetailed(
            ingest_external_experiment_results.asyncio_detailed, str(run_id), client=self._client, body=body
        )
        return _typed_result(response, ExternalRunResultsResponse)

    async def compare(self, body: RunComparisonRequest) -> RunComparisonResponse:
        response = await _adetailed(compare_experiment_runs.asyncio_detailed, client=self._client, body=body)
        return _typed_result(response, RunComparisonResponse)
