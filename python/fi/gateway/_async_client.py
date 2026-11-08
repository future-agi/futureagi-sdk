"""The asynchronous client, :class:`AsyncAgentCC`."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any
from typing_extensions import Self as _Self

from fi.gateway._client_common import ClientState, CostLedger, derived_options, resource_property
from fi.gateway._constants import DEFAULT_MAX_RETRIES, NOT_GIVEN
from fi.gateway._env import resolve_api_key, resolve_base_url
from fi.gateway._http_security import reject_credential_query
from fi.gateway._session import SessionContext
from fi.gateway._transport._pool import HttpPool

__all__ = ["AsyncAgentCC"]

if TYPE_CHECKING:
    from fi.gateway.resources.audio import AsyncAudio
    from fi.gateway.resources.batches import AsyncBatches
    from fi.gateway.resources.moderations import AsyncModerations
    from fi.gateway.resources.chat import AsyncChat
    from fi.gateway.resources.completions import AsyncCompletions
    from fi.gateway.resources.embeddings import AsyncEmbeddings
    from fi.gateway.resources.files import AsyncFiles
    from fi.gateway.resources.images import AsyncImages
    from fi.gateway.resources.models import AsyncModels
    from fi.gateway.resources.rerank import AsyncRerank
    from fi.gateway.resources.responses import AsyncResponses

_R = "fi.gateway.resources"


from fi.gateway._deprecation import deprecated_options


@deprecated_options("redact_messages", "pre_call_rules", "modify_params", "enable_json_schema_validation", "callbacks")
class AsyncAgentCC(ClientState):
    """Asynchronous client for the AgentCC LLM Gateway.

    ``callback_mode='snapshot'`` opts into detached absolute-URL requests and
    JSON response bodies without gateway metadata. Published descriptors remain
    the default. ``expanded_callback_events=True`` enables additional cache,
    cost, fallback, guardrail and session hooks. Copies retain these options.
    ``metadata_mode='merge'`` enables layered metadata and JSON session headers;
    the default retains replacement and per-key session headers.
    ``audio_upload_mode='normalized'`` opts into string paths and repeated list
    form fields; published string content and multipart serialization remain
    the default, with additive explicit ``Path`` support.

    Usage::

        from fi.gateway import AsyncAgentCC

        client = AsyncAgentCC(api_key="sk-...", base_url="https://gateway.example.com")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | Any | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, str] | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: Any = None,
        callbacks: list[Any] | None = None,
        http_client: Any = None,
        drop_params: bool = False,
        retry_policy: Any = None,
        redact_messages: bool = False,
        pre_call_rules: list[Any] | None = None,
        modify_params: bool = False,
        enable_json_schema_validation: bool = False,
        callback_mode: str = "published",
        expanded_callback_events: bool = False,
        metadata_mode: str = "replace",
        audio_upload_mode: str = "published",
    ) -> None:
        reject_credential_query(default_query)
        self._api_key = resolve_api_key(api_key)
        self._base_url = resolve_base_url(base_url)

        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers = default_headers
        self._default_query = default_query
        self._session_id = session_id
        self._metadata = metadata
        self._init_metadata_mode(metadata_mode)
        self._init_audio_upload_mode(audio_upload_mode)
        self._config = config
        self._callbacks = callbacks
        self._init_callback_options(callback_mode, expanded_callback_events)
        self._http_client = http_client
        self._drop_params = drop_params
        self._retry_policy = retry_policy
        self._enable_json_schema_validation = enable_json_schema_validation

        self._base_client: Any = None
        self._chat: Any = None
        self._models: Any = None
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
        self._init_compat(redact_messages, pre_call_rules, modify_params)
        self._batches: Any = None
        self._moderations: Any = None

    def session(
        self,
        session_id: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        path: str | None = None,
    ) -> SessionContext:
        """Create a session context that sets the session headers on model requests.

        Inside it, chat completions (``create`` and ``stream``), completions,
        ``responses.create``, audio (speech, transcriptions, translations) and
        ``files.create`` send the session's id, name, path and metadata. Embeddings,
        images, rerank, models and the other ``files`` and ``responses`` calls send the
        client's headers only, as in agentcc 1.x.

        ``path`` is where the session starts (``"/checkout"``; default ``"/"``);
        ``sess.step(name)`` extends it.

        Usage::

            async with client.session(name="research") as sess:
                sess.step("search")
                await client.chat.completions.create(...)
        """
        from fi.gateway._session import SessionContext

        return SessionContext(
            self, session_id=session_id, name=name, metadata=metadata, path=path
        )

    def _get_base_client(self) -> Any:
        if self._base_client is None:
            from fi.gateway._transport._async import AsyncBaseClient

            self._base_client = AsyncBaseClient(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
                default_headers=self._default_headers,
                default_query=self._default_query,
                session_id=self._session_id,
                metadata=self._metadata,
                metadata_mode=self._metadata_mode,
                config=self._config,
                callbacks=self._callbacks,
                http_client=self._http_client,
                retry_policy=self._retry_policy,
                on_cost=self._cost.add,
                pool=self._pool,
                redact_messages=self._redact_messages,
                owner=self,
            )
        return self._base_client

    if TYPE_CHECKING:  # what type checkers see; at runtime each is built on first use

        @property
        def chat(self) -> AsyncChat:
            ...

        @property
        def models(self) -> AsyncModels:
            ...

        @property
        def embeddings(self) -> AsyncEmbeddings:
            ...

        @property
        def images(self) -> AsyncImages:
            ...

        @property
        def audio(self) -> AsyncAudio:
            ...

        @property
        def completions(self) -> AsyncCompletions:
            ...

        @property
        def rerank(self) -> AsyncRerank:
            ...

        @property
        def responses(self) -> AsyncResponses:
            ...

        @property
        def files(self) -> AsyncFiles:
            ...

        @property
        def batches(self) -> AsyncBatches:
            ...

        @property
        def moderations(self) -> AsyncModerations:
            ...

    else:
        batches = resource_property("_batches", f"{_R}.batches", "AsyncBatches")
        moderations = resource_property("_moderations", f"{_R}.moderations", "AsyncModerations")
        chat = resource_property("_chat", f"{_R}.chat", "AsyncChat")
        models = resource_property("_models", f"{_R}.models", "AsyncModels")
        embeddings = resource_property(
            "_embeddings", f"{_R}.embeddings", "AsyncEmbeddings"
        )
        images = resource_property("_images", f"{_R}.images", "AsyncImages")
        audio = resource_property("_audio", f"{_R}.audio", "AsyncAudio")
        completions = resource_property(
            "_completions", f"{_R}.completions", "AsyncCompletions"
        )
        rerank = resource_property("_rerank", f"{_R}.rerank", "AsyncRerank")
        responses = resource_property("_responses", f"{_R}.responses", "AsyncResponses")
        files = resource_property("_files", f"{_R}.files", "AsyncFiles")

    @property
    def current_cost(self) -> float:
        """Cumulative ``x-agentcc-cost`` (USD) across the responses this client received.

        Shared with every ``with_options()`` copy. A response without the header adds
        nothing; a streamed response counts the cost its headers carry.
        """
        return self._cost.total

    def _track_cost(self, cost: float) -> None:
        """Add cost from a completed request."""
        self._cost.add(cost)

    def reset_cost(self) -> None:
        """Reset the cumulative cost tracker to zero."""
        self._cost.reset()

    def with_options(
        self,
        *,
        timeout: Any = NOT_GIVEN,
        max_retries: Any = NOT_GIVEN,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, str] | None = None,
        session_id: Any = NOT_GIVEN,
        metadata: Any = NOT_GIVEN,
        trace_id: Any = NOT_GIVEN,
        drop_params: Any = NOT_GIVEN,
    ) -> _Self:
        """Return a same-class client with merged options, sharing the connection pool.

        The copy sends with its own options (each one not given is carried over) and
        adds to the same ``current_cost``. An initialized transport's pool is shared and remains
        owned by the parent. A copy made before first use owns its independent pool
        and closes it itself, preserving the released lifecycle. ``extra_headers`` and ``extra_query`` are added
        over this client's ``default_headers`` and ``default_query`` (the copy's value
        wins for a key both set); every request the copy sends carries them.
        """
        new = type(self)(
            **derived_options(
                self,
                timeout=timeout,
                max_retries=max_retries,
                extra_headers=extra_headers,
                extra_query=extra_query,
                session_id=session_id,
                metadata=metadata,
                trace_id=trace_id,
                drop_params=drop_params,
            )
        )
        new._cost = self._cost
        new._user_copied = True
        if self._base_client is not None or self._pool.client is not None:
            new._pool = self._pool
            new._shares_pool = True
        return new

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool (a ``with_options()`` copy leaves it
        open; a client passed as ``http_client`` is never closed)."""
        if not self._shares_pool:
            await self._pool.aclose()

    async def __aenter__(self) -> AsyncAgentCC:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        key = self._api_key
        key_preview = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        return f"AsyncAgentCC(base_url={self._base_url!r}, api_key={key_preview!r})"
