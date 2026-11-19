import copy
import dataclasses
import functools
import inspect
import json
import sys
import threading
import warnings
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Callable, Literal, TypeVar
from urllib.parse import quote
from uuid import UUID

import httpx

from fi._core.core_http import (
    AsyncMappedClient,
    MappedClient,
    check_redirect,
    invalid_json,
)
from fi._core.errors import api_error
from fi._credentials import Credentials, MissingAuthError
from fi._credentials import resolve as resolve_credentials
from fi._extra_headers import ExtraHeaders
from fi._http import DEFAULT_TIMEOUT, ClientRetryingTransport, LazyKeyAuth
from fi._queue_create import FACADE_DEFAULT_QUEUE_CALL, FACADE_DEFAULT_QUEUE_METHOD
from fi._queue_create import create_body as queue_create_body
from fi._queue_create import default_queue_body
from fi._sdk_exception import SDKException  # noqa: F401  (kept importable from here)
from fi.errors import FutureAGIAPIError  # defined in fi.errors; re-exported here
from fi.knowledge_bases import KnowledgeBasesClient
from fi.prompts import PromptsClient
from fi.scores import ScoresClient
from fi.generated.openapi_client.api.annotation_queue_discussion import (
    create_annotation_queue_item_comment,
    list_annotation_queue_item_discussion,
    reopen_annotation_queue_item_thread,
    resolve_annotation_queue_item_thread,
    toggle_annotation_queue_item_comment_reaction,
)
from fi.generated.openapi_client.api.annotation_queue_items import (
    add_annotation_queue_items,
    assign_annotation_queue_items,
    complete_annotation_queue_item,
    get_annotation_queue_item_detail,
    get_next_annotation_queue_item,
    import_annotation_queue_item_annotations,
    list_annotation_queue_item_annotations,
    list_annotation_queue_items,
    release_annotation_queue_item,
    remove_annotation_queue_items,
    skip_annotation_queue_item,
    submit_annotation_queue_item_annotations,
)
from fi.generated.openapi_client.api.annotation_queue_review import (
    review_annotation_queue_item,
)
from fi.generated.openapi_client.api.annotation_queues import (
    add_annotation_queue_label,
    archive_annotation_queue,
    create_annotation_queue,
    export_annotation_queue,
    export_annotation_queue_to_dataset,
    get_annotation_queue,
    get_annotation_queue_agreement,
    get_annotation_queue_analytics,
    get_annotation_queue_progress,
    list_annotation_queue_export_fields,
    list_annotation_queues,
    remove_annotation_queue_label,
    update_annotation_queue,
    update_annotation_queue_status,
)
from fi.generated.openapi_client.api.dataset_versions import (
    create_dataset_version,
    get_dataset_version,
    list_dataset_versions,
)
from fi.generated.openapi_client.api.experiment_runs import (
    compare_experiment_runs,
    create_external_experiment_run,
    ingest_external_experiment_results,
)
from fi.generated.openapi_client.api.model_hub import (
    model_hub_annotation_queues_get_or_create_default,
)
from fi.generated.openapi_client.client import Client as GeneratedOpenAPIClient
from fi.generated.openapi_client.models.add_items import AddItems
from fi.generated.openapi_client.models.annotation_queue import (
    AnnotationQueue as GeneratedAnnotationQueue,
)
from fi.generated.openapi_client.models.assign_items import AssignItems
from fi.generated.openapi_client.models.bulk_remove_items import BulkRemoveItems
from fi.generated.openapi_client.models.dataset_version_create import (
    DatasetVersionCreate,
)
from fi.generated.openapi_client.models.dataset_version_create_response import (
    DatasetVersionCreateResponse,
)
from fi.generated.openapi_client.models.dataset_version_detail_response import (
    DatasetVersionDetailResponse,
)
from fi.generated.openapi_client.models.dataset_version_list_response import (
    DatasetVersionListResponse,
)
from fi.generated.openapi_client.models.discussion_comment_request import (
    DiscussionCommentRequest,
)
from fi.generated.openapi_client.models.discussion_reaction_request import (
    DiscussionReactionRequest,
)
from fi.generated.openapi_client.models.discussion_thread_status_request import (
    DiscussionThreadStatusRequest,
)
from fi.generated.openapi_client.models.empty_request import EmptyRequest
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
from fi.generated.openapi_client.models.import_annotations import ImportAnnotations
from fi.generated.openapi_client.models.list_annotation_queue_items_ordering import (
    ListAnnotationQueueItemsOrdering,
)
from fi.generated.openapi_client.models.queue_default_request import (
    QueueDefaultRequest,
)
from fi.generated.openapi_client.models.queue_export_to_dataset_request import (
    QueueExportToDatasetRequest,
)
from fi.generated.openapi_client.models.queue_item_navigation_request import (
    QueueItemNavigationRequest,
)
from fi.generated.openapi_client.models.queue_label_request import QueueLabelRequest
from fi.generated.openapi_client.models.queue_status_request import QueueStatusRequest
from fi.generated.openapi_client.models.review_item_request import ReviewItemRequest
from fi.generated.openapi_client.models.run_comparison_request import (
    RunComparisonRequest,
)
from fi.generated.openapi_client.models.run_comparison_response import (
    RunComparisonResponse,
)
from fi.generated.openapi_client.models.submit_annotations import SubmitAnnotations
from fi.generated.openapi_client.types import Response as GeneratedResponse
from fi.generated.platform.catalog.models import Models
from fi.tracing import TracingClient
from fi.generated.platform.catalog.optimizations import Optimizations
from fi.generated.platform.catalog.workspaces import Workspaces

T = TypeVar("T")


def _typed_result(response: GeneratedResponse[Any], expected: type[T]) -> T:
    if response.status_code >= 400:
        raise _status_error(response)
    if not isinstance(response.parsed, expected):
        raise FutureAGIAPIError(int(response.status_code), "Unexpected response shape")
    return response.parsed


def _generated_kwargs(module: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Keep free-form paging kwargs on the wire even when typed operations omit them."""
    paging = {"page", "limit", "page_size", "page_number", "offset", "cursor",
              "cursor_mode", "current_page_index", "page_token"}
    declared = inspect.signature(module._get_kwargs).parameters
    extra = {k: v for k, v in kwargs.items() if k in paging and k not in declared}
    request = module._get_kwargs(*args, **{k: v for k, v in kwargs.items() if k not in extra})
    if extra:
        request["params"] = {**request.get("params", {}), **_clean(extra)}
    return request


def _detailed(
    sync_detailed: Callable[..., Any],
    *args: Any,
    client: GeneratedOpenAPIClient,
    **kwargs: Any,
) -> GeneratedResponse[Any]:
    """``sync_detailed(*args, client=client, **kwargs)``, except that an error status is returned
    unparsed. The generated ``_parse_response`` parses every error body as JSON, so an HTML 502 or
    503 from a proxy raised ``JSONDecodeError``; ``_status_error`` reads the raw body instead. A 3xx
    is ``UnexpectedRedirectError`` (never followed, never parsed)."""
    module = sys.modules[sync_detailed.__module__]
    response = client.get_httpx_client().request(**_generated_kwargs(module, args, kwargs))
    check_redirect(response, module.__name__.rsplit(".", 1)[-1])
    if response.status_code >= 400:
        return _unparsed(response)
    return _parsed(module, client, response)


async def _adetailed(
    asyncio_detailed: Callable[..., Any],
    *args: Any,
    client: GeneratedOpenAPIClient,
    **kwargs: Any,
) -> GeneratedResponse[Any]:
    """The async twin of :func:`_detailed`."""
    module = sys.modules[asyncio_detailed.__module__]
    response = await client.get_async_httpx_client().request(
        **_generated_kwargs(module, args, kwargs)
    )
    check_redirect(response, module.__name__.rsplit(".", 1)[-1])
    if response.status_code >= 400:
        return _unparsed(response)
    return _parsed(module, client, response)


def _parsed(
    module: Any, client: GeneratedOpenAPIClient, response: httpx.Response
) -> GeneratedResponse[Any]:
    """The generated parse of a success response; a body that is not JSON is a typed error
    (``code="invalid_json"``) that is still a ``ValueError``, as the generated parse's was. Any other
    ``ValueError`` (a JSON body whose enum or date does not parse) propagates unchanged, as before."""
    try:
        return module._build_response(client=client, response=response)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise invalid_json(response) from None


def _unparsed(response: httpx.Response) -> GeneratedResponse[Any]:
    try:
        status: Any = HTTPStatus(response.status_code)
    except ValueError:  # a non-standard status (a CDN's 520)
        status = response.status_code
    return GeneratedResponse(
        status_code=status,
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def _status_error(response: GeneratedResponse[Any]) -> FutureAGIAPIError:
    """The typed error for a generated response's status: the same class a platform
    namespace raises for it. An undeclared status (no parsed model) reads the raw body."""
    wire_body = _body_payload(response.content)
    # Model conversion is not authority for the exact regional wire envelope.
    regional = int(response.status_code) == 403 and isinstance(wire_body, dict) and wire_body.get("error") == "wrong_region"
    if response.parsed is not None:
        payload = _to_plain(response.parsed)
    else:
        payload = wire_body
    return api_error(int(response.status_code), payload, response.headers, regional=regional)


def _body_payload(content: bytes) -> Any:
    if not content:
        return None
    try:
        return json.loads(content)
    except ValueError:
        return content.decode("utf-8", "replace")


class _GeneratedClient(GeneratedOpenAPIClient):
    """The generated client on httpx clients whose connection failures are typed
    (``fi._core.core_http``: ``APIConnectionError`` / ``APITimeoutError`` that are still the httpx
    errors they replace). Everything else is the generated client's own behaviour."""

    def get_httpx_client(self) -> httpx.Client:
        if self._client is None:
            self._client = MappedClient(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=self._headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **self._httpx_args,
            )
        return self._client

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = AsyncMappedClient(
                base_url=self._base_url,
                cookies=self._cookies,
                headers=self._headers,
                timeout=self._timeout,
                verify=self._verify_ssl,
                follow_redirects=self._follow_redirects,
                **self._httpx_args,
            )
        return self._async_client


def _as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _clean(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _quote(value: str | UUID) -> str:
    return quote(str(value), safe="")


def _coerce_model(model: type[T], value: Mapping[str, Any] | T | None) -> T:
    if isinstance(value, model):
        return value
    if value is None:
        value = {}
    return model.from_dict(value)  # type: ignore[attr-defined]


def _to_plain(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _to_plain(value.to_dict())
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_plain(item) for item in value)
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


def _ordering(
    value: str | ListAnnotationQueueItemsOrdering | None,
) -> ListAnnotationQueueItemsOrdering | None:
    if value is None or isinstance(value, ListAnnotationQueueItemsOrdering):
        return value
    return ListAnnotationQueueItemsOrdering(value)


class FutureAGIClient:
    """The typed platform client.

    Simulation APIs are not offered in this release.

    - Keys are resolved on the first request (``fi._credentials``: arguments, then the environment,
      then one saved login bound to its base URL), so constructing a client never raises.
    - Requests use a default ``httpx.Timeout(30, connect=10)`` and a retrying transport
      (429 and pre-send connect errors for every method; 502/503/504 and other network errors for
      idempotent methods only, so a POST create is never repeated after a 5xx; ``Retry-After``
      honoured; ``fi._http``).
    - Two origins, one set of credentials: ``base_url`` serves the core namespaces;
      the platform origin (``platform_base_url`` / ``FI_PLATFORM_BASE_URL``, else derived as
      ``{base_url}/omega/api``) serves the platform namespaces, which send ``workspace_id`` /
      ``organization_id`` as selectors when set. ``platform_token`` is a self-hosted EE's Bearer
      token. The platform origin is resolved, and its host guard run, on the first platform call
      (``fi._core.origins``), so a bad platform setting never breaks a core namespace.
    - Nonloopback HTTP with a platform Bearer token requires ``allow_insecure_http=True``
      (else ``FI_ALLOW_INSECURE_HTTP=1``); explicit False overrides the environment. Keys-mode
      HTTP warns about future refusal.
    - Errors are typed on every namespace (``fi.errors``): each status maps to one class, and a
      failure with no response raises ``APIConnectionError`` / ``APITimeoutError``.
    - ``with_options(timeout=..., retries=...)`` returns a copy that shares the connection pool.
    - ``FI_EXTRA_HEADERS`` (``Name=value`` entries) and ``extra_headers=`` (which wins per name) are
      sent on every request to ``base_url`` and never to another host (``fi._extra_headers``), on core
      and platform namespaces alike: a platform origin under ``base_url`` (the derived
      ``{base_url}/omega/api``) gets them, one elsewhere does not.
    """

    # FA catalog namespaces, bound in _build_namespaces by fi._core.catalog_registration.
    workspaces: Workspaces
    optimizations: Optimizations
    models: Models

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        fi_api_key: str | None = None,
        fi_secret_key: str | None = None,
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
        explicit_api = api_key or fi_api_key
        explicit_secret = secret_key or fi_secret_key
        resolved = resolve_credentials(explicit_api, explicit_secret, base_url)
        self.base_url = resolved.base_url
        self._options = _ClientOptions(
            explicit_api,
            explicit_secret,
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
        # FI_EXTRA_HEADERS, with extra_headers= winning per name: every request to base_url, never another host
        self._extra_headers = ExtraHeaders(self.base_url, extra_headers)
        self._management_lock = threading.Lock()

        def _require() -> Credentials:
            creds = resolve_credentials(explicit_api, explicit_secret, self.base_url)
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
        # one transport for the sync and the async httpx client (both get httpx_args)
        self._build_namespaces(
            ClientRetryingTransport(retries=retries), _as_timeout(timeout)
        )

    def _build_namespaces(
        self, transport: ClientRetryingTransport, timeout: httpx.Timeout
    ) -> None:
        self.generated_client = _GeneratedClient(
            base_url=self.base_url,
            headers=dict(self._options.headers),
            timeout=timeout,
            # an undeclared status (a 429 or 503 the spec omits) is mapped by _status_error, never
            # raised as the generated client's UnexpectedStatus
            raise_on_unexpected_status=False,
            httpx_args={"auth": self._auth, "transport": transport},
        )
        from fi.environments import Environments
        self.__dict__.pop("agents", None)
        self.environments = Environments(self)
        self.knowledge_bases = KnowledgeBasesClient(self.generated_client)
        self.prompts = PromptsClient(self.generated_client)
        self.scores = ScoresClient(self.generated_client)
        self.annotation_labels = self.scores.labels
        self.annotation_queues = AnnotationQueuesClient(self.generated_client)
        self.datasets = DatasetsClient(self.generated_client)
        self.evals = EvalsClient(self.generated_client, lambda: self._auth.credentials)
        self.experiments_v2 = ExperimentsClient(self.generated_client)
        self.experiment_runs = ExperimentRunsClient(self.generated_client)
        self.tracing = TracingClient(self)
        self.users = UsersClient(self.generated_client)
        self.alerts = AlertsClient(self.generated_client)
        from fi._core.catalog_registration import register
        register(self)

    @property
    def experiments(self) -> "ExperimentsClient":
        """Deprecated alias of :attr:`experiments_v2` (``fi.experiments`` is the run engine)."""
        warnings.warn(
            "FutureAGIClient.experiments is renamed experiments_v2; the old name will be removed.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.experiments_v2

    @property
    def auth(self) -> Credentials:
        """The SDK's own resolved keys and base URL (raises ``MissingAuthError`` when there are no
        keys). Named ``auth`` so it is not confused with ``client.workspace.secrets`` or the gateway's
        provider credentials."""
        return self._auth.credentials

    @property
    def api_key(self) -> str | None:
        return resolve_credentials_for(self).api_key

    @property
    def secret_key(self) -> str | None:
        return resolve_credentials_for(self).secret_key

    def close(self) -> None:
        self.evals._close()
        self.generated_client.get_httpx_client().close()
        for name in ("_platform", "_management"):
            if name in self.__dict__ and not self._options.copy:
                self.__dict__[name].shared.close()

    def __enter__(self) -> "FutureAGIClient":
        self.generated_client.__enter__()
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.evals._close()
        self.generated_client.__exit__(*args, **kwargs)
        for name in ("_platform", "_management"):
            if name in self.__dict__ and not self._options.copy:
                self.__dict__[name].shared.close()

    @property
    def gateway(self) -> Any:
        """Gateway management with personal platform credentials (not the model-call client)."""
        from fi.generated.platform.fa_management.gateway import Gateway
        return Gateway(self._management)

    @functools.cached_property
    def _management(self) -> Any:
        from fi._core.fa_registration import get_core
        return get_core(self)

    @property
    def connectors(self) -> Any:
        """Workspace MCP connections; OAuth completion remains in the browser."""
        from fi.connectors import Connectors
        return Connectors(self)

    @property
    def integrations(self) -> Any:
        """Data connections and their sync history."""
        from fi.integrations import Integrations
        return Integrations(self)

    @property
    def credentials(self) -> Any:
        """Workspace credential metadata, never credential mutations."""
        from fi.credentials import Credentials
        return Credentials(self)

    @functools.cached_property
    def agents(self) -> Any:
        """Managed agents and runs using this client's platform settings."""
        from fi.agents import Agents
        return Agents(self)

    @functools.cached_property
    def _platform(self) -> Any:
        """The platform executor (``fi._core.platform_base``), built on first use; namespaces call it."""
        from fi._core.platform_base import PlatformCore
        from fi._core.transport import PlatformShared, Settings
        from fi._core.connector_policy import OPERATIONS as CONNECTOR_OPERATIONS

        return PlatformCore(
            PlatformShared(
                self._resolve_platform_origin,
                retries=self._options.retries,
                supplemental_table=CONNECTOR_OPERATIONS,
                extra_headers=self._extra_headers,
            ),
            Settings(timeout=self._options.timeout),
        )

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

    def with_options(
        self,
        *,
        timeout: float | httpx.Timeout | None = None,
        retries: int | None = None,
    ) -> "FutureAGIClient":
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
        old = self.generated_client._httpx_args["transport"]
        inner, inner_async = shared_inner(old)
        transport = ClientRetryingTransport(
            retries=clone._options.retries, wrapped=inner, wrapped_async=inner_async
        )
        clone._build_namespaces(transport, clone._options.timeout)
        clone.__dict__["_platform"] = self._platform.with_settings(
            timeout=timeout, retries=retries
        )
        return clone


@dataclasses.dataclass(frozen=True)
class _ClientOptions:
    """What the constructor was given, kept for the platform origin and ``with_options``."""

    api_key: str | None = dataclasses.field(repr=False)
    secret_key: str | None = dataclasses.field(repr=False)
    headers: dict[str, str] = dataclasses.field(repr=False)
    timeout: httpx.Timeout
    retries: int
    platform_base_url: str | None = None
    workspace_id: str | None = None
    organization_id: str | None = None
    platform_token: str | None = dataclasses.field(default=None, repr=False)
    allow_custom_platform_url: bool | None = None
    copy: bool = False
    allow_insecure_http: bool | None = None


def _as_timeout(timeout: float | httpx.Timeout | None) -> httpx.Timeout:
    if timeout is None:
        return DEFAULT_TIMEOUT
    if isinstance(timeout, httpx.Timeout):
        return timeout
    return httpx.Timeout(float(timeout), connect=min(10.0, float(timeout)))


def creds_missing(creds: Credentials) -> Exception:
    try:
        creds.require()
    except Exception as exc:  # CredentialsMissingError
        return exc
    return RuntimeError("credentials missing")


def resolve_credentials_for(client: "FutureAGIClient") -> Credentials:
    try:
        return client._auth.credentials
    except MissingAuthError:
        return resolve_credentials(None, None, client.base_url)


class BaseGeneratedClient:
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        self._client = client

    def _request(
        self, sync_detailed: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        response = _detailed(sync_detailed, *args, client=self._client, **kwargs)
        if int(response.status_code) >= 400:
            raise _status_error(response)
        return _to_plain(response.parsed)

    def _raw_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Any = None,
    ) -> Any:
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": path,
            "params": _clean(query or {}),
        }
        if body is not None:
            request_kwargs["json"] = body
        response = self._client.get_httpx_client().request(**request_kwargs)
        check_redirect(response, f"{method.upper()} {path}")
        status_code = int(response.status_code)
        if response.content:
            try:
                payload: Any = response.json()
            except ValueError:
                payload = response.text
        else:
            payload = None
        if status_code >= 400:
            raise api_error(status_code, payload, response.headers)
        return payload


class AnnotationQueuesClient(BaseGeneratedClient):
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        super().__init__(client)
        self.items = AnnotationQueueItemsClient(client)
        self.discussion = AnnotationQueueDiscussionClient(client)
        self.review = AnnotationQueueReviewClient(client)

    def list(self, **query: Any) -> Any:
        """Pagination: page_size (page size); limit (page size); page (1-based). page_size is a supported size alias; limit takes precedence when both are supplied."""
        return self._request(list_annotation_queues.sync_detailed, **_clean(query))

    def create(self, body: Mapping[str, Any] | GeneratedAnnotationQueue) -> Any:
        """Create an annotation queue (POST /model-hub/annotation-queues/).

        ``body`` needs ``name``. Supply ``label_ids`` with at least one annotation label id.
        Omitting labels emits one ``DeprecationWarning`` and reuses ``get_or_create_default``
        with exactly one of ``project``, ``dataset`` or ``agent_definition`` to obtain labels.
        That lookup can create or restore the default queue even if the label check then
        fails, but never invents labels or scopes the new queue. No single scope or no usable
        labels on its default queue raises ``fi.queues.DefaultQueueLabelError`` (also exported
        from ``fi``, a ``ValueError`` subclass). Explicit
        ``None`` or empty labels remain invalid. Label and annotator ids are
        UUIDs; another value raises ``ValueError`` naming this call. ``annotator_roles`` maps a
        user id in ``annotator_ids`` to a role
        or a list of roles. ``project``, ``dataset`` and ``agent_definition`` are read-only
        on the server and never applied on create: with explicit labels they are dropped
        with a ``DeprecationWarning`` and remain accepted for compatibility. For the
        default queue of a project, dataset or agent definition, call
        ``get_or_create_default``; ``project_id``, ``dataset_id`` or ``agent_definition_id`` in
        the body (or in a generated model's ``additional_properties``) raise ``ValueError``
        naming that call: the server never applies them to the queue (it only uses them to
        scope its duplicate-name check).
        """
        payload = queue_create_body(
            body.to_dict() if isinstance(body, GeneratedAnnotationQueue) else body,
            caller="annotation_queues.create()",
            instead=FACADE_DEFAULT_QUEUE_CALL,
            default_call=FACADE_DEFAULT_QUEUE_METHOD,
            stacklevel=2,
            uuid_ids=True,
            get_default=self.get_or_create_default,
        )
        roles = payload.pop("annotator_roles", None)
        model = _coerce_model(GeneratedAnnotationQueue, payload)
        if roles is not None:
            # The generated model reads the serializer's JSONField child as an object, but the
            # server takes a role or a list of roles per user id, so the mapping is sent as given.
            roles = roles.to_dict() if hasattr(roles, "to_dict") else roles
            model.additional_properties["annotator_roles"] = {
                str(user_id): user_roles for user_id, user_roles in dict(roles).items()
            }
        return self._request(create_annotation_queue.sync_detailed, body=model)

    def get_or_create_default(
        self,
        *,
        project_id: str | UUID | None = None,
        dataset_id: str | UUID | None = None,
        agent_definition_id: str | UUID | None = None,
    ) -> Any:
        """The default annotation queue of a project, dataset or agent definition.

        POST /model-hub/annotation-queues/get-or-create-default/. Give exactly one id, a UUID
        (``str`` or ``UUID``); anything else raises ``ValueError`` naming this call before any
        request (``TypeError`` when the value is neither a string nor a UUID). The server
        returns the active default queue, restores an archived one, or creates it, with its
        labels. Default queues are open to every member of the organization.

        Returns the response body as a plain ``dict``, like the other methods of this client:
        ``{"status": True, "result": {"queue": {...}, "labels": [...], "created": bool,
        "action": "fetched" | "restored" | "created"}}``.
        """
        body = default_queue_body(
            caller="annotation_queues.get_or_create_default()",
            uuid_ids=True,
            project_id=project_id,
            dataset_id=dataset_id,
            agent_definition_id=agent_definition_id,
        )
        return self._request(
            model_hub_annotation_queues_get_or_create_default.sync_detailed,
            body=QueueDefaultRequest.from_dict(body),
        )

    def get(self, queue_id: str | UUID) -> Any:
        return self._request(get_annotation_queue.sync_detailed, _as_uuid(queue_id))

    def update(
        self, queue_id: str | UUID, body: Mapping[str, Any] | GeneratedAnnotationQueue
    ) -> Any:
        return self._request(
            update_annotation_queue.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(GeneratedAnnotationQueue, body),
        )

    def archive(self, queue_id: str | UUID) -> Any:
        return self._request(archive_annotation_queue.sync_detailed, _as_uuid(queue_id))

    def update_status(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueStatusRequest
    ) -> Any:
        return self._request(
            update_annotation_queue_status.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueStatusRequest, body),
        )

    def progress(self, queue_id: str | UUID) -> Any:
        return self._request(get_annotation_queue_progress.sync_detailed, str(queue_id))

    def analytics(self, queue_id: str | UUID) -> Any:
        return self._request(
            get_annotation_queue_analytics.sync_detailed, str(queue_id)
        )

    def agreement(self, queue_id: str | UUID) -> Any:
        return self._request(
            get_annotation_queue_agreement.sync_detailed, str(queue_id)
        )

    def export_json(self, queue_id: str | UUID) -> Any:
        return self._request(export_annotation_queue.sync_detailed, str(queue_id))

    def list_export_fields(self, queue_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_export_fields.sync_detailed, str(queue_id)
        )

    def export_to_dataset(
        self,
        queue_id: str | UUID,
        body: Mapping[str, Any] | QueueExportToDatasetRequest,
    ) -> Any:
        return self._request(
            export_annotation_queue_to_dataset.sync_detailed,
            str(queue_id),
            body=_coerce_model(QueueExportToDatasetRequest, body),
        )

    def add_label(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueLabelRequest
    ) -> Any:
        return self._request(
            add_annotation_queue_label.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueLabelRequest, body),
        )

    def remove_label(
        self, queue_id: str | UUID, body: Mapping[str, Any] | QueueLabelRequest
    ) -> Any:
        return self._request(
            remove_annotation_queue_label.sync_detailed,
            _as_uuid(queue_id),
            body=_coerce_model(QueueLabelRequest, body),
        )


class AnnotationQueueItemsClient(BaseGeneratedClient):
    def list(self, queue_id: str | UUID, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        if "ordering" in query:
            query["ordering"] = _ordering(query["ordering"])
        return self._request(
            list_annotation_queue_items.sync_detailed, str(queue_id), **_clean(query)
        )

    def add(self, queue_id: str | UUID, body: Mapping[str, Any] | AddItems) -> Any:
        return self._request(
            add_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(AddItems, body),
        )

    def assign(
        self, queue_id: str | UUID, body: Mapping[str, Any] | AssignItems
    ) -> Any:
        return self._request(
            assign_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(AssignItems, body),
        )

    def remove(
        self, queue_id: str | UUID, body: Mapping[str, Any] | BulkRemoveItems
    ) -> Any:
        return self._request(
            remove_annotation_queue_items.sync_detailed,
            str(queue_id),
            body=_coerce_model(BulkRemoveItems, body),
        )

    def next(self, queue_id: str | UUID, **query: Any) -> Any:
        """Pagination: no supported paging parameters. Use exclude or before for item navigation, not numbered pages."""
        return self._request(
            get_next_annotation_queue_item.sync_detailed, str(queue_id), **_clean(query)
        )

    def get_detail(
        self, queue_id: str | UUID, item_id: str | UUID, **query: Any
    ) -> Any:
        return self._request(
            get_annotation_queue_item_detail.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            **_clean(query),
        )

    def release(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | EmptyRequest | None = None,
    ) -> Any:
        return self._request(
            release_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(EmptyRequest, body),
        )

    def complete(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | QueueItemNavigationRequest | None = None,
    ) -> Any:
        return self._request(
            complete_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(QueueItemNavigationRequest, body),
        )

    def skip(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | QueueItemNavigationRequest | None = None,
    ) -> Any:
        return self._request(
            skip_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(QueueItemNavigationRequest, body),
        )

    def list_annotations(self, queue_id: str | UUID, item_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
        )

    def submit_annotations(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | SubmitAnnotations,
    ) -> Any:
        return self._request(
            submit_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(SubmitAnnotations, body),
        )

    def import_annotations(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | ImportAnnotations,
    ) -> Any:
        return self._request(
            import_annotation_queue_item_annotations.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(ImportAnnotations, body),
        )


class AnnotationQueueDiscussionClient(BaseGeneratedClient):
    def list(self, queue_id: str | UUID, item_id: str | UUID) -> Any:
        return self._request(
            list_annotation_queue_item_discussion.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
        )

    def comment(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | DiscussionCommentRequest,
    ) -> Any:
        return self._request(
            create_annotation_queue_item_comment.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(DiscussionCommentRequest, body),
        )

    def resolve_thread(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        thread_id: str,
        body: Mapping[str, Any] | DiscussionThreadStatusRequest | None = None,
    ) -> Any:
        return self._request(
            resolve_annotation_queue_item_thread.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            thread_id,
            body=_coerce_model(DiscussionThreadStatusRequest, body),
        )

    def reopen_thread(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        thread_id: str,
        body: Mapping[str, Any] | DiscussionThreadStatusRequest | None = None,
    ) -> Any:
        return self._request(
            reopen_annotation_queue_item_thread.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            thread_id,
            body=_coerce_model(DiscussionThreadStatusRequest, body),
        )

    def react(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        comment_id: str,
        body: Mapping[str, Any] | DiscussionReactionRequest,
    ) -> Any:
        return self._request(
            toggle_annotation_queue_item_comment_reaction.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            comment_id,
            body=_coerce_model(DiscussionReactionRequest, body),
        )


class AnnotationQueueReviewClient(BaseGeneratedClient):
    def submit(
        self,
        queue_id: str | UUID,
        item_id: str | UUID,
        body: Mapping[str, Any] | ReviewItemRequest,
    ) -> Any:
        return self._request(
            review_annotation_queue_item.sync_detailed,
            str(queue_id),
            _as_uuid(item_id),
            body=_coerce_model(ReviewItemRequest, body),
        )


class DatasetVersionsClient(BaseGeneratedClient):
    """Immutable snapshots. Create makes one attempt and has no retry key."""

    def list(
        self, dataset_id: str | UUID, *, limit: int = 100, offset: int = 0
    ) -> DatasetVersionListResponse:
        """Pagination: limit (page size); offset (0-based)."""
        return _typed_result(
            _detailed(
                list_dataset_versions.sync_detailed,
                str(dataset_id),
                client=self._client,
                limit=limit,
                offset=offset,
            ),
            DatasetVersionListResponse,
        )

    def get(
        self,
        dataset_id: str | UUID,
        version_id: str | UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> DatasetVersionDetailResponse:
        """Pagination: limit (page size); offset (0-based)."""
        return _typed_result(
            _detailed(
                get_dataset_version.sync_detailed,
                str(dataset_id),
                str(version_id),
                client=self._client,
                limit=limit,
                offset=offset,
            ),
            DatasetVersionDetailResponse,
        )

    def create(
        self, dataset_id: str | UUID, body: DatasetVersionCreate
    ) -> DatasetVersionCreateResponse:
        return _typed_result(
            _detailed(
                create_dataset_version.sync_detailed,
                str(dataset_id),
                client=self._client,
                body=body,
            ),
            DatasetVersionCreateResponse,
        )

    def export_jsonl(self, dataset_id: str | UUID, version_id: str | UUID) -> str:
        """Return one complete bounded archive; failures return no partial text."""
        from fi.datasets.version_jsonl import (
            MAX_BYTES,
            MAX_ITEMS,
            case_records_size,
            encode_version_jsonl,
        )

        items: list[dict[str, Any]] = []
        version = None
        received_bytes = 0
        while True:
            page = self.get(
                dataset_id, version_id, limit=500, offset=len(items)
            ).result.to_dict()
            current = page["version"]
            if str(UUID(str(current.get("id")))) != str(UUID(str(version_id))) or str(
                UUID(str(current.get("dataset")))
            ) != str(UUID(str(dataset_id))):
                raise ValueError("Version page does not match requested identity")
            if version is not None and current != version:
                raise ValueError("Version metadata changed between pages")
            version = current
            count = version.get("item_count")
            if type(count) is not int or not 0 <= count <= MAX_ITEMS:
                raise ValueError(f"Version must contain 0–{MAX_ITEMS} cases")
            if page["offset"] != len(items) or (page["has_more"] and not page["items"]):
                raise ValueError("Version pagination is incomplete")
            received_bytes += case_records_size(page["items"])
            if received_bytes > MAX_BYTES:
                raise ValueError("Version pages exceed archive byte limit")
            items.extend(page["items"])
            if len(items) > count or (page["has_more"] and len(items) >= count):
                raise ValueError("Version pagination exceeds declared item_count")
            if not page["has_more"]:
                return encode_version_jsonl(version, items)

    def import_jsonl(
        self,
        dataset_id: str | UUID,
        source: str | bytes,
        *,
        parent_version_id: str | UUID | None = None,
        legacy_rows: Literal["reject", "preserve", "drop"] = "reject",
    ) -> DatasetVersionCreateResponse:
        """Validate all records, then make one non-idempotent snapshot POST."""
        from fi.datasets.version_jsonl import decode_version_jsonl

        return self.create(
            dataset_id,
            decode_version_jsonl(
                source,
                dataset_id,
                parent_version_id=parent_version_id,
                legacy_rows=legacy_rows,
            ),
        )


class DatasetExternalMetricsClient(BaseGeneratedClient):
    """Metrics for scores computed outside the platform (SRV-5). The server never runs them.

    ``create`` is create-or-reuse: the same (dataset, name, source_hash, scoring definition)
    returns the same ``metric_id``; any change gives a new metric. 200 on both.
    """

    def create(self, dataset_id: str | UUID, body: Mapping[str, Any]) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/datasets/{_quote(dataset_id)}/external-metrics/",
            body=dict(body),
        )

    def list(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/datasets/{_quote(dataset_id)}/external-metrics/",
            query=query,
        )


class DatasetsClient(BaseGeneratedClient):
    def __init__(self, client: GeneratedOpenAPIClient) -> None:
        super().__init__(client)
        self.versions = DatasetVersionsClient(client)
        self.external_metrics = DatasetExternalMetricsClient(client)

    def list(self, **query: Any) -> Any:
        """Pagination: page (0-based); page_size (page size)."""
        return self._raw_request(
            "GET", "/model-hub/develops/get-datasets/", query=query
        )

    def list_names(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/model-hub/develops/get-datasets-names/", query=query
        )

    def get_table(self, dataset_id: str | UUID, **query: Any) -> Any:
        """Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token)."""
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/get-dataset-table/",
            query=query,
        )

    def get_row(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/get-row-data/",
            body=body,
        )

    def get_columns(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/dataset/columns/{_quote(dataset_id)}/"
        )

    def create_empty(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-empty-dataset/", body=body
        )

    def create_manual(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-dataset-manually/", body=body
        )

    def create_from_file(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/develops/create-dataset-from-local-file/", body=body
        )

    def add_rows(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_rows/",
            body=body,
        )

    def add_columns(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_columns/",
            body=body,
        )

    def update_cell(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/update_cell_value/",
            body=body,
        )

    def delete_row(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_row/",
            query=query,
        )

    def delete_column(self, dataset_id: str | UUID, column_id: str | UUID) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_column/{_quote(column_id)}/",
        )

    def download(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/download_dataset/",
            query=query,
        )

    def json_schema(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/dataset/{_quote(dataset_id)}/json-schema/"
        )

    def eval_stats(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/dataset/{_quote(dataset_id)}/eval-stats/",
            query=query,
        )

    def annotation_summary(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/dataset/{_quote(dataset_id)}/annotation-summary/",
            query=query,
        )

    def duplicate(self, dataset_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/datasets/{_quote(dataset_id)}/duplicate/",
            body=body,
        )

    def derived_variables(self, dataset_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/datasets/{_quote(dataset_id)}/derived-variables/"
        )

    def base_columns(self, **query: Any) -> Any:
        return self._raw_request(
            "GET", "/model-hub/datasets/get-base-columns/", query=query
        )


class ExperimentRunsClient(BaseGeneratedClient):
    """Persist caller-executed evidence; replay requires unchanged IDs and payload."""

    def create(self, body: ExternalRunCreateRequest) -> ExternalRunCreateResponse:
        return _typed_result(
            _detailed(
                create_external_experiment_run.sync_detailed,
                client=self._client,
                body=body,
            ),
            ExternalRunCreateResponse,
        )

    def ingest_results(
        self, run_id: str | UUID, body: ExternalRunResultsRequest
    ) -> ExternalRunResultsResponse:
        return _typed_result(
            _detailed(
                ingest_external_experiment_results.sync_detailed,
                str(run_id),
                client=self._client,
                body=body,
            ),
            ExternalRunResultsResponse,
        )

    def compare(self, body: RunComparisonRequest) -> RunComparisonResponse:
        return _typed_result(
            _detailed(
                compare_experiment_runs.sync_detailed, client=self._client, body=body
            ),
            RunComparisonResponse,
        )

    def get(self, run_id: str | UUID) -> Any:
        """One run: the create header, ``plan_size`` and ``item_counts`` (SRV-3)."""
        return self._raw_request(
            "GET", f"/model-hub/experiment-runs/{_quote(run_id)}/"
        )

    def list_items(
        self,
        run_id: str | UUID,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        max_value_bytes: int | None = None,
    ) -> Any:
        """One page of recorded items in plan order (SRV-3). ``status`` is comma-separated
        (``"failed,skipped"``); ``limit * max_value_bytes`` may be at most 4 MiB.

        Pagination: limit (page size); offset (0-based)."""
        return self._raw_request(
            "GET",
            f"/model-hub/experiment-runs/{_quote(run_id)}/items/",
            query={
                "status": status,
                "limit": limit,
                "offset": offset,
                "max_value_bytes": max_value_bytes,
            },
        )


class ExperimentsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return self._raw_request("GET", "/model-hub/experiments/v2/list/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/experiments/v2/", body=body)

    def get(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/",
            query=query,
        )

    def update(self, experiment_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/",
            body=body,
        )

    def delete(self, body: Any) -> Any:
        return self._raw_request(
            "DELETE", "/model-hub/experiments/v2/delete/", body=body
        )

    def rows(self, experiment_id: str | UUID, **query: Any) -> Any:
        """Pagination: page_size (page size); current_page_index (0-based)."""
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/rows/",
            query=query,
        )

    def row(self, experiment_id: str | UUID, row_id: str | UUID, **query: Any) -> Any:
        """Pagination: page_size (page size); current_page_index (0-based)."""
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/rows/{_quote(row_id)}/",
            query=query,
        )

    def stats(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/stats/",
            query=query,
        )

    def download(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/download/",
            query=query,
        )

    def rerun(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/experiments/v2/re-run/", body=body)

    def stop(self, experiment_id: str | UUID, body: Any | None = None) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/stop/",
            body=body,
        )

    def compare(self, experiment_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/compare-experiments/",
            body=body,
        )

    def comparisons(self, experiment_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/experiments/v2/{_quote(experiment_id)}/comparisons/",
            query=query,
        )

    def json_schema(self, experiment_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/experiments/v2/{_quote(experiment_id)}/json-schema/"
        )


class EvalsClient(BaseGeneratedClient):
    def __init__(
        self,
        client: GeneratedOpenAPIClient,
        credentials: Callable[[], Credentials] | None = None,
    ) -> None:
        import threading

        super().__init__(client)
        self._credentials = credentials
        self._delegate: Any = None
        self._delegate_lock = threading.Lock()
        self._closed = False

    def evaluate(self, eval_templates: Any, inputs: Any, **kwargs: Any) -> Any:
        """Run ``fi.evals.Evaluator.evaluate`` with this client's resolved HTTP configuration."""
        with self._delegate_lock:
            if self._closed:
                raise RuntimeError("the evaluation client is closed")
            if self._delegate is None:
                if self._credentials is None:
                    raise TypeError("this EvalsClient was built without credentials; use FutureAGIClient().evals")
                from fi.evals._delegate import EvaluatorDelegate

                self._delegate = EvaluatorDelegate(self._credentials, self._client.get_httpx_client)
            delegate = self._delegate
        return delegate.evaluate(eval_templates, inputs, **kwargs)

    def _close(self) -> None:
        with self._delegate_lock:
            self._closed = True
            delegate = self._delegate
        if delegate is not None:
            delegate.close()

    def list_templates(self, body: Any) -> Any:
        """Pagination: page (0-based); page_size (page size). Pass these in the request body."""
        return self._raw_request("POST", "/model-hub/eval-templates/list/", body=body)

    def create_template(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/eval-templates/create-v2/", body=body
        )

    def get_template(self, template_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/detail/"
        )

    def update_template(self, template_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/eval-templates/{_quote(template_id)}/update/",
            body=body,
        )

    def delete_template(self, body: Any) -> Any:
        return self._raw_request("POST", "/model-hub/delete-eval-template/", body=body)

    def bulk_delete_templates(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/model-hub/eval-templates/bulk-delete/", body=body
        )

    def template_usage(self, template_id: str | UUID) -> Any:
        """Pagination: page (0-based); page_size (page size). This facade uses the default page; use the low-level operation to supply pagination parameters."""
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/usage/"
        )

    def template_versions(self, template_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", f"/model-hub/eval-templates/{_quote(template_id)}/versions/"
        )

    def create_template_version(self, template_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/create/",
            body=body,
        )

    def restore_template_version(
        self,
        template_id: str | UUID,
        version_id: str | UUID,
        body: Any | None = None,
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/{_quote(version_id)}/restore/",
            body=body or {},
        )

    def set_default_template_version(
        self,
        template_id: str | UUID,
        version_id: str | UUID,
        body: Any | None = None,
    ) -> Any:
        return self._raw_request(
            "PUT",
            f"/model-hub/eval-templates/{_quote(template_id)}/versions/{_quote(version_id)}/set-default/",
            body=body or {},
        )

    def list_sdk_evals(self) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/get-evals/")

    def new_eval(self, body: Any) -> Any:
        """Run one platform template by name (``POST /sdk/api/v1/new-eval/``)."""
        return self._raw_request("POST", "/sdk/api/v1/new-eval/", body=body)

    def configure(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/sdk/api/v1/configure-evaluations/", body=body
        )

    def run(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/eval/", body=body)

    def get_run(self, eval_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/sdk/api/v1/eval/{_quote(eval_id)}/")

    def run_v2(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/new-eval/", body=body)

    def get_run_v2(self, eval_id: str | UUID) -> Any:
        return self._raw_request(
            "GET", "/sdk/api/v1/new-eval/", query={"eval_id": eval_id}
        )

    def list_pipelines(self, **query: Any) -> Any:
        return self._raw_request("GET", "/sdk/api/v1/evaluate-pipeline/", query=query)

    def evaluate_pipeline(self, body: Any) -> Any:
        return self._raw_request("POST", "/sdk/api/v1/evaluate-pipeline/", body=body)

    def dataset_evals(self, dataset_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/get_evals_list/",
            query=query,
        )

    def dataset_eval_structure(
        self, dataset_id: str | UUID, eval_id: str | UUID, **query: Any
    ) -> Any:
        return self._raw_request(
            "GET",
            f"/model-hub/develops/{_quote(dataset_id)}/get_eval_structure/{_quote(eval_id)}/",
            query=query,
        )

    def preview_dataset_eval(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/preview_run_eval/",
            body=body,
        )

    def start_dataset_evals(self, dataset_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/start_evals_process/",
            body=body,
        )

    def add_dataset_user_eval(self, dataset_id: str | UUID, body: Any) -> Any:
        """Selecting Turing/Protect models requires an Enterprise licence including those models on
        self-hosted servers; cloud plan checks are separate. A self-hosted model-gate denial
        raises PaymentRequiredError (HTTP 402 ENTITLEMENT_DENIED), not LicenseRequiredError.
        Select another model or ask the server administrator to enable the licensed models.
        Code evaluations are exempt from this model gate."""
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/add_user_eval/",
            body=body,
        )

    def edit_and_run_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID, body: Any
    ) -> Any:
        """Selecting Turing/Protect models requires an Enterprise licence including those models on
        self-hosted servers; cloud plan checks are separate. A self-hosted model-gate denial
        raises PaymentRequiredError (HTTP 402 ENTITLEMENT_DENIED), not LicenseRequiredError.
        Select another model or ask the server administrator to enable the licensed models.
        Code evaluations are exempt from this model gate."""
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/edit_and_run_user_eval/{_quote(eval_id)}/",
            body=body,
        )

    def stop_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID, body: Any | None = None
    ) -> Any:
        return self._raw_request(
            "POST",
            f"/model-hub/develops/{_quote(dataset_id)}/stop_user_eval/{_quote(eval_id)}/",
            body=body or {},
        )

    def delete_dataset_user_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_user_eval/{_quote(eval_id)}/",
        )

    def delete_dataset_template_eval(
        self, dataset_id: str | UUID, eval_id: str | UUID
    ) -> Any:
        return self._raw_request(
            "DELETE",
            f"/model-hub/develops/{_quote(dataset_id)}/delete_template_eval/{_quote(eval_id)}/",
        )


class UsersClient(BaseGeneratedClient):
    def current(self) -> Any:
        return self._raw_request("GET", "/accounts/user-info/")

    def organization_members(self, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return self._raw_request("GET", "/accounts/organization/members/", query=query)

    def workspaces(self, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return self._raw_request("GET", "/accounts/workspace/list/", query=query)

    def workspace_members(self, workspace_id: str | UUID, **query: Any) -> Any:
        """Pagination: page (1-based); limit (page size)."""
        return self._raw_request(
            "GET", f"/accounts/workspace/{_quote(workspace_id)}/members/", query=query
        )

    def switch_workspace(self, body: Any) -> Any:
        return self._raw_request("POST", "/accounts/workspace/switch/", body=body)


class AlertsClient(BaseGeneratedClient):
    def list(self, **query: Any) -> Any:
        """Pagination: page_number (0-based); page_size (page size)."""
        return self._raw_request("GET", "/tracer/user-alerts/", query=query)

    def create(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alerts/", body=body)

    def get(self, alert_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/user-alerts/{_quote(alert_id)}/")

    def update(self, alert_id: str | UUID, body: Any) -> Any:
        return self._raw_request(
            "PATCH", f"/tracer/user-alerts/{_quote(alert_id)}/", body=body
        )

    def delete(self, alert_id: str | UUID) -> Any:
        return self._raw_request("DELETE", f"/tracer/user-alerts/{_quote(alert_id)}/")

    def metric_options(self, **query: Any) -> Any:
        """Pagination: no supported paging parameters."""
        return self._raw_request(
            "GET", "/tracer/user-alerts/metric-options/", query=query
        )

    def preview_graph(self, body: Any) -> Any:
        return self._raw_request(
            "POST", "/tracer/user-alerts/preview-graph/", body=body
        )

    def graph(self, alert_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET", f"/tracer/user-alerts/{_quote(alert_id)}/graph/", query=query
        )

    def details(self, alert_id: str | UUID, **query: Any) -> Any:
        """Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs list."""
        return self._raw_request(
            "GET", f"/tracer/user-alerts/{_quote(alert_id)}/details/", query=query
        )

    def bulk_mute(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alerts/bulk-mute/", body=body)

    def logs(self, **query: Any) -> Any:
        """Pagination: limit (page size); page (1-based)."""
        return self._raw_request("GET", "/tracer/user-alert-logs/", query=query)

    def all_logs(self, **query: Any) -> Any:
        """Pagination: no supported paging parameters."""
        return self._raw_request("GET", "/tracer/user-alert-logs/all/", query=query)

    def log(self, log_id: str | UUID) -> Any:
        return self._raw_request("GET", f"/tracer/user-alert-logs/{_quote(log_id)}/")

    def logs_for_alert(self, alert_id: str | UUID, **query: Any) -> Any:
        return self._raw_request(
            "GET", f"/tracer/user-alert-logs/{_quote(alert_id)}/list/", query=query
        )

    def resolve_logs(self, body: Any) -> Any:
        return self._raw_request("POST", "/tracer/user-alert-logs/resolve/", body=body)
