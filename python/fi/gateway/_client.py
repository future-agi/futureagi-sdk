"""The synchronous client, :class:`AgentCC`; the async client remains split."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any
from typing_extensions import Self as _Self

from fi.gateway._async_client import AsyncAgentCC
from fi.gateway._client_common import ClientState, CostLedger, derived_options, resource_property
from fi.gateway._constants import DEFAULT_MAX_RETRIES, NOT_GIVEN
from fi.gateway._env import resolve_base_url
from fi.gateway._secrets import _Secret, client_key
from fi.gateway._http_security import reject_credential_query
from fi.gateway._session import SessionContext
from fi.gateway._transport._pool import HttpPool

__all__ = ["AgentCC", "AsyncAgentCC"]

if TYPE_CHECKING:
    from fi.gateway.resources.audio import Audio
    from fi.gateway.resources.batches import Batches
    from fi.gateway.resources.chat import Chat
    from fi.gateway.resources.completions import Completions
    from fi.gateway.resources.embeddings import Embeddings
    from fi.gateway.resources.files import Files
    from fi.gateway.resources.images import Images
    from fi.gateway.resources.models import Models
    from fi.gateway.resources.moderations import Moderations
    from fi.gateway.resources.rerank import Rerank
    from fi.gateway.resources.responses import Responses

_R = "fi.gateway.resources"


from fi.gateway._deprecation import deprecated_options


@deprecated_options("redact_messages", "pre_call_rules", "modify_params", "enable_json_schema_validation", "callbacks")
class AgentCC(ClientState):
    """Synchronous gateway client requiring a virtual key and explicit origin.

    Callbacks use the published relative request descriptor and model response
    body. ``callback_mode='snapshot'`` opts into detached absolute-URL requests
    and JSON response bodies without gateway metadata. Set
    ``expanded_callback_events=True`` to enable cache, cost, fallback, guardrail
    and session notifications in addition to the published request/stream hooks.
    ``metadata_mode='merge'`` explicitly enables client/session/request dictionary
    layering and JSON session metadata; the default replaces request metadata and
    keeps the published per-key session headers, including on option copies.
    ``audio_upload_mode='normalized'`` opts into string paths and repeated list
    form fields. By default strings remain upload content; use ``Path`` to read
    a local file without changing the published multipart serialization.
    """

    def __init__(
        self, *, api_key: str | None = None, base_url: str | None = None,
        timeout: float | Any | None = None, max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, str] | None = None,
        session_id: str | None = None, metadata: dict[str, Any] | None = None,
        config: Any = None, callbacks: list[Any] | None = None,
        http_client: Any = None, drop_params: bool = False, retry_policy: Any = None,
        redact_messages: bool = False, pre_call_rules: list[Any] | None = None,
        modify_params: bool = False, enable_json_schema_validation: bool = False,
        callback_mode: str = "published", expanded_callback_events: bool = False,
        metadata_mode: str = "replace", audio_upload_mode: str = "published",
    ) -> None:
        # Keep constructor aliases opaque even when validation raises.
        api_key = _Secret.hold(api_key)
        default_headers = _Secret.hold(default_headers)
        config = _Secret.hold(config)
        reject_credential_query(default_query)
        self._api_key = client_key(api_key)
        self._base_url = resolve_base_url(base_url)
        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers = _Secret.hold(default_headers)
        self._default_query = default_query
        self._session_id = session_id
        self._metadata = metadata
        self._init_metadata_mode(metadata_mode)
        self._init_audio_upload_mode(audio_upload_mode)
        self._config = _Secret.hold(config)
        self._callbacks = callbacks
        self._init_callback_options(callback_mode, expanded_callback_events)
        self._http_client = http_client
        self._drop_params = drop_params
        self._retry_policy = retry_policy
        self._enable_json_schema_validation = enable_json_schema_validation
        self._init_compat(redact_messages, pre_call_rules, modify_params)
        self._base_client: Any = None
        self._chat: Any = None
        self._models: Any = None
        self._batches: Any = None
        self._moderations: Any = None
        self._embeddings: Any = None
        self._images: Any = None
        self._audio: Any = None
        self._completions: Any = None
        self._rerank: Any = None
        self._responses: Any = None
        self._files: Any = None
        self._lock = threading.Lock()
        self._user_copied = False
        self._shares_pool = False
        self._cost = CostLedger()
        self._pool = HttpPool(http_client)

    def session(
        self, session_id: str | None = None, name: str | None = None,
        metadata: dict[str, Any] | None = None, path: str | None = None,
    ) -> SessionContext:
        """Bind session headers and accounting to the current thread/context."""
        return SessionContext(self, session_id=session_id, name=name, metadata=metadata, path=path)

    def _get_base_client(self) -> Any:
        if self._base_client is None:
            from fi.gateway._transport._sync import SyncBaseClient

            self._base_client = SyncBaseClient(
                api_key=self._api_key, base_url=self._base_url, timeout=self._timeout,
                max_retries=self._max_retries, default_headers=self._default_headers,
                default_query=self._default_query, session_id=self._session_id,
                metadata=self._metadata, config=self._config, metadata_mode=self._metadata_mode,
                callbacks=self._callbacks,
                http_client=self._http_client, retry_policy=self._retry_policy,
                on_cost=self._cost.add, pool=self._pool,
                redact_messages=self._redact_messages, owner=self,
            )
        return self._base_client

    if TYPE_CHECKING:
        @property
        def chat(self) -> Chat: ...
        @property
        def models(self) -> Models: ...
        @property
        def batches(self) -> Batches: ...
        @property
        def moderations(self) -> Moderations: ...
        @property
        def embeddings(self) -> Embeddings: ...
        @property
        def images(self) -> Images: ...
        @property
        def audio(self) -> Audio: ...
        @property
        def completions(self) -> Completions: ...
        @property
        def rerank(self) -> Rerank: ...
        @property
        def responses(self) -> Responses: ...
        @property
        def files(self) -> Files: ...
    else:
        chat = resource_property("_chat", f"{_R}.chat", "Chat")
        models = resource_property("_models", f"{_R}.models", "Models")
        batches = resource_property("_batches", f"{_R}.batches", "Batches")
        moderations = resource_property("_moderations", f"{_R}.moderations", "Moderations")
        embeddings = resource_property("_embeddings", f"{_R}.embeddings", "Embeddings")
        images = resource_property("_images", f"{_R}.images", "Images")
        audio = resource_property("_audio", f"{_R}.audio", "Audio")
        completions = resource_property("_completions", f"{_R}.completions", "Completions")
        rerank = resource_property("_rerank", f"{_R}.rerank", "Rerank")
        responses = resource_property("_responses", f"{_R}.responses", "Responses")
        files = resource_property("_files", f"{_R}.files", "Files")

    @property
    def current_cost(self) -> float:
        """Cumulative gateway cost, shared by with_options copies."""
        return self._cost.total

    def _track_cost(self, cost: float) -> None:
        self._cost.add(cost)

    def reset_cost(self) -> None:
        self._cost.reset()

    def with_options(
        self, *, timeout: Any = NOT_GIVEN, max_retries: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, str] | None = None, session_id: Any = NOT_GIVEN,
        metadata: Any = NOT_GIVEN, trace_id: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
    ) -> _Self:
        """Copy options and cost accounting; share an initialized transport's pool.

        A copy made before the first use owns and closes its independent pool,
        preserving the released lifecycle. Caller-provided HTTP clients stay shared.
        """
        new = type(self)(**derived_options(
            self, timeout=timeout, max_retries=max_retries,
            extra_headers=extra_headers, extra_query=extra_query, session_id=session_id,
            metadata=metadata, trace_id=trace_id, drop_params=drop_params,
        ))
        new._cost = self._cost
        new._user_copied = True
        if self._base_client is not None or self._pool.client is not None:
            new._pool = self._pool
            new._shares_pool = True
        return new

    def close(self) -> None:
        """Close only an SDK-owned pool; option copies do not own their shared pool."""
        if not self._shares_pool:
            self._pool.close()

    def __enter__(self) -> AgentCC:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        key_preview = self._api_key.key_preview()
        return f"AgentCC(base_url={self._base_url!r}, api_key={key_preview!r})"
