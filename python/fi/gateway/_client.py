"""Public AgentCC and AsyncAgentCC client classes."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from typing import Any

from fi.gateway._constants import DEFAULT_MAX_RETRIES, NOT_GIVEN


class AgentCC:
    """Synchronous client for the AgentCC LLM Gateway.

    Usage::

        from fi.gateway import AgentCC

        client = AgentCC(api_key="sk-...", base_url="https://gateway.example.com")
        response = client.chat.completions.create(
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
        pre_call_rules: list[Callable] | None = None,
        modify_params: bool = False,
        enable_json_schema_validation: bool = False,
    ) -> None:
        from fi.gateway._exceptions import AgentCCError

        self._api_key = api_key or os.environ.get("AGENTCC_API_KEY") or ""
        if not self._api_key:
            raise AgentCCError(
                "api_key is required. Pass it as a parameter or set the AGENTCC_API_KEY environment variable."
            )

        self._base_url = base_url or os.environ.get("AGENTCC_BASE_URL") or ""
        if not self._base_url:
            raise AgentCCError(
                "base_url is required. Pass it as a parameter or set the AGENTCC_BASE_URL environment variable."
            )

        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers = default_headers
        self._default_query = default_query
        self._session_id = session_id
        self._metadata = metadata
        self._config = config
        self._callbacks = callbacks
        self._http_client = http_client
        self._drop_params = drop_params
        self._retry_policy = retry_policy
        self._redact_messages = redact_messages
        self._pre_call_rules = pre_call_rules
        self._modify_params = modify_params
        self._enable_json_schema_validation = enable_json_schema_validation

        self._base_client: Any = None
        self._chat: Any = None
        self._models: Any = None
        self._batches: Any = None
        self._embeddings: Any = None
        self._images: Any = None
        self._audio: Any = None
        self._completions: Any = None
        self._moderations: Any = None
        self._rerank: Any = None
        self._responses: Any = None
        self._files: Any = None
        self._lock = threading.Lock()
        self._user_copied = False
        self._current_cost: float = 0.0
        self._cost_lock = threading.Lock()
        self._active_session: Any = None

    @property
    def redact_messages(self) -> bool:
        """Whether message content should be redacted before sending."""
        return self._redact_messages

    @redact_messages.setter
    def redact_messages(self, value: bool) -> None:
        self._redact_messages = value

    def session(
        self,
        session_id: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create a session context that auto-sets session headers on all requests.

        Usage::

            with client.session(name="research") as sess:
                sess.step("search")
                client.chat.completions.create(...)
        """
        from fi.gateway._session import SessionContext

        return SessionContext(self, session_id=session_id, name=name, metadata=metadata)

    def _get_base_client(self) -> Any:
        if self._base_client is None:
            from fi.gateway._base_client import SyncBaseClient

            self._base_client = SyncBaseClient(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
                default_headers=self._default_headers,
                default_query=self._default_query,
                session_id=self._session_id,
                metadata=self._metadata,
                config=self._config,
                callbacks=self._callbacks,
                http_client=self._http_client,
                retry_policy=self._retry_policy,
            )
        return self._base_client

    @property
    def chat(self) -> Any:
        if self._chat is None:
            with self._lock:
                if self._chat is None:
                    from fi.gateway.resources.chat import Chat

                    self._chat = Chat(self)
        return self._chat

    @property
    def models(self) -> Any:
        if self._models is None:
            with self._lock:
                if self._models is None:
                    from fi.gateway.resources.models import Models

                    self._models = Models(self)
        return self._models

    @property
    def batches(self) -> Any:
        if self._batches is None:
            with self._lock:
                if self._batches is None:
                    from fi.gateway.resources.batches import Batches

                    self._batches = Batches(self)
        return self._batches

    @property
    def embeddings(self) -> Any:
        if self._embeddings is None:
            with self._lock:
                if self._embeddings is None:
                    from fi.gateway.resources.embeddings import Embeddings

                    self._embeddings = Embeddings(self)
        return self._embeddings

    @property
    def images(self) -> Any:
        if self._images is None:
            with self._lock:
                if self._images is None:
                    from fi.gateway.resources.images import Images

                    self._images = Images(self)
        return self._images

    @property
    def audio(self) -> Any:
        if self._audio is None:
            with self._lock:
                if self._audio is None:
                    from fi.gateway.resources.audio import Audio

                    self._audio = Audio(self)
        return self._audio

    @property
    def completions(self) -> Any:
        if self._completions is None:
            with self._lock:
                if self._completions is None:
                    from fi.gateway.resources.completions import Completions

                    self._completions = Completions(self)
        return self._completions

    @property
    def moderations(self) -> Any:
        if self._moderations is None:
            with self._lock:
                if self._moderations is None:
                    from fi.gateway.resources.moderations import Moderations

                    self._moderations = Moderations(self)
        return self._moderations

    @property
    def rerank(self) -> Any:
        if self._rerank is None:
            with self._lock:
                if self._rerank is None:
                    from fi.gateway.resources.rerank import Rerank

                    self._rerank = Rerank(self)
        return self._rerank

    @property
    def responses(self) -> Any:
        if self._responses is None:
            with self._lock:
                if self._responses is None:
                    from fi.gateway.resources.responses import Responses

                    self._responses = Responses(self)
        return self._responses

    @property
    def files(self) -> Any:
        if self._files is None:
            with self._lock:
                if self._files is None:
                    from fi.gateway.resources.files import Files

                    self._files = Files(self)
        return self._files

    @property
    def current_cost(self) -> float:
        """Cumulative cost across all API calls."""
        return self._current_cost

    def _track_cost(self, cost: float) -> None:
        """Add cost from a completed request."""
        with self._cost_lock:
            self._current_cost += cost

    def reset_cost(self) -> None:
        """Reset the cumulative cost tracker to zero."""
        with self._cost_lock:
            self._current_cost = 0.0

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
    ) -> AgentCC:
        """Return a new client with merged configuration, sharing the connection pool."""
        new_headers = dict(self._default_headers or {})
        if extra_headers:
            new_headers.update(extra_headers)

        new_query = dict(self._default_query or {})
        if extra_query:
            new_query.update(extra_query)

        new = AgentCC(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=timeout if timeout is not NOT_GIVEN else self._timeout,
            max_retries=max_retries if max_retries is not NOT_GIVEN else self._max_retries,
            default_headers=new_headers or None,
            default_query=new_query or None,
            session_id=session_id if session_id is not NOT_GIVEN else self._session_id,
            metadata=metadata if metadata is not NOT_GIVEN else self._metadata,
            config=self._config,
            callbacks=self._callbacks,
            http_client=self._http_client,
            drop_params=drop_params if drop_params is not NOT_GIVEN else self._drop_params,
            pre_call_rules=self._pre_call_rules,
            modify_params=self._modify_params,
            enable_json_schema_validation=self._enable_json_schema_validation,
        )
        # Share the underlying HTTP client
        if self._base_client is not None:
            new._base_client = self._base_client
        new._user_copied = True
        return new

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        if self._base_client is not None and not self._user_copied:
            self._base_client.close()

    def __enter__(self) -> AgentCC:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        key = self._api_key
        key_preview = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        return f"AgentCC(base_url={self._base_url!r}, api_key={key_preview!r})"


class AsyncAgentCC:
    """Asynchronous client for the AgentCC LLM Gateway.

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
        pre_call_rules: list[Callable] | None = None,
        modify_params: bool = False,
        enable_json_schema_validation: bool = False,
    ) -> None:
        from fi.gateway._exceptions import AgentCCError

        self._api_key = api_key or os.environ.get("AGENTCC_API_KEY") or ""
        if not self._api_key:
            raise AgentCCError(
                "api_key is required. Pass it as a parameter or set the AGENTCC_API_KEY environment variable."
            )

        self._base_url = base_url or os.environ.get("AGENTCC_BASE_URL") or ""
        if not self._base_url:
            raise AgentCCError(
                "base_url is required. Pass it as a parameter or set the AGENTCC_BASE_URL environment variable."
            )

        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers = default_headers
        self._default_query = default_query
        self._session_id = session_id
        self._metadata = metadata
        self._config = config
        self._callbacks = callbacks
        self._http_client = http_client
        self._drop_params = drop_params
        self._retry_policy = retry_policy
        self._redact_messages = redact_messages
        self._pre_call_rules = pre_call_rules
        self._modify_params = modify_params
        self._enable_json_schema_validation = enable_json_schema_validation

        self._base_client: Any = None
        self._chat: Any = None
        self._models: Any = None
        self._batches: Any = None
        self._embeddings: Any = None
        self._images: Any = None
        self._audio: Any = None
        self._completions: Any = None
        self._moderations: Any = None
        self._rerank: Any = None
        self._responses: Any = None
        self._files: Any = None
        self._lock = threading.Lock()
        self._user_copied = False
        self._current_cost: float = 0.0
        self._cost_lock = threading.Lock()
        self._active_session: Any = None

    @property
    def redact_messages(self) -> bool:
        """Whether message content should be redacted before sending."""
        return self._redact_messages

    @redact_messages.setter
    def redact_messages(self, value: bool) -> None:
        self._redact_messages = value

    def session(
        self,
        session_id: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Create a session context that auto-sets session headers on all requests.

        Usage::

            async with client.session(name="research") as sess:
                sess.step("search")
                await client.chat.completions.create(...)
        """
        from fi.gateway._session import SessionContext

        return SessionContext(self, session_id=session_id, name=name, metadata=metadata)

    def _get_base_client(self) -> Any:
        if self._base_client is None:
            from fi.gateway._base_client import AsyncBaseClient

            self._base_client = AsyncBaseClient(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
                default_headers=self._default_headers,
                default_query=self._default_query,
                session_id=self._session_id,
                metadata=self._metadata,
                config=self._config,
                callbacks=self._callbacks,
                http_client=self._http_client,
                retry_policy=self._retry_policy,
            )
        return self._base_client

    @property
    def chat(self) -> Any:
        if self._chat is None:
            with self._lock:
                if self._chat is None:
                    from fi.gateway.resources.chat import AsyncChat

                    self._chat = AsyncChat(self)
        return self._chat

    @property
    def models(self) -> Any:
        if self._models is None:
            with self._lock:
                if self._models is None:
                    from fi.gateway.resources.models import AsyncModels

                    self._models = AsyncModels(self)
        return self._models

    @property
    def batches(self) -> Any:
        if self._batches is None:
            with self._lock:
                if self._batches is None:
                    from fi.gateway.resources.batches import AsyncBatches

                    self._batches = AsyncBatches(self)
        return self._batches

    @property
    def embeddings(self) -> Any:
        if self._embeddings is None:
            with self._lock:
                if self._embeddings is None:
                    from fi.gateway.resources.embeddings import AsyncEmbeddings

                    self._embeddings = AsyncEmbeddings(self)
        return self._embeddings

    @property
    def images(self) -> Any:
        if self._images is None:
            with self._lock:
                if self._images is None:
                    from fi.gateway.resources.images import AsyncImages

                    self._images = AsyncImages(self)
        return self._images

    @property
    def audio(self) -> Any:
        if self._audio is None:
            with self._lock:
                if self._audio is None:
                    from fi.gateway.resources.audio import AsyncAudio

                    self._audio = AsyncAudio(self)
        return self._audio

    @property
    def completions(self) -> Any:
        if self._completions is None:
            with self._lock:
                if self._completions is None:
                    from fi.gateway.resources.completions import AsyncCompletions

                    self._completions = AsyncCompletions(self)
        return self._completions

    @property
    def moderations(self) -> Any:
        if self._moderations is None:
            with self._lock:
                if self._moderations is None:
                    from fi.gateway.resources.moderations import AsyncModerations

                    self._moderations = AsyncModerations(self)
        return self._moderations

    @property
    def rerank(self) -> Any:
        if self._rerank is None:
            with self._lock:
                if self._rerank is None:
                    from fi.gateway.resources.rerank import AsyncRerank

                    self._rerank = AsyncRerank(self)
        return self._rerank

    @property
    def responses(self) -> Any:
        if self._responses is None:
            with self._lock:
                if self._responses is None:
                    from fi.gateway.resources.responses import AsyncResponses

                    self._responses = AsyncResponses(self)
        return self._responses

    @property
    def files(self) -> Any:
        if self._files is None:
            with self._lock:
                if self._files is None:
                    from fi.gateway.resources.files import AsyncFiles

                    self._files = AsyncFiles(self)
        return self._files

    @property
    def current_cost(self) -> float:
        """Cumulative cost across all API calls."""
        return self._current_cost

    def _track_cost(self, cost: float) -> None:
        """Add cost from a completed request."""
        with self._cost_lock:
            self._current_cost += cost

    def reset_cost(self) -> None:
        """Reset the cumulative cost tracker to zero."""
        with self._cost_lock:
            self._current_cost = 0.0

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
    ) -> AsyncAgentCC:
        new_headers = dict(self._default_headers or {})
        if extra_headers:
            new_headers.update(extra_headers)

        new_query = dict(self._default_query or {})
        if extra_query:
            new_query.update(extra_query)

        new = AsyncAgentCC(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=timeout if timeout is not NOT_GIVEN else self._timeout,
            max_retries=max_retries if max_retries is not NOT_GIVEN else self._max_retries,
            default_headers=new_headers or None,
            default_query=new_query or None,
            session_id=session_id if session_id is not NOT_GIVEN else self._session_id,
            metadata=metadata if metadata is not NOT_GIVEN else self._metadata,
            config=self._config,
            callbacks=self._callbacks,
            http_client=self._http_client,
            drop_params=drop_params if drop_params is not NOT_GIVEN else self._drop_params,
            pre_call_rules=self._pre_call_rules,
            modify_params=self._modify_params,
            enable_json_schema_validation=self._enable_json_schema_validation,
        )
        if self._base_client is not None:
            new._base_client = self._base_client
        new._user_copied = True
        return new

    async def aclose(self) -> None:
        if self._base_client is not None and not self._user_copied:
            await self._base_client.aclose()

    async def __aenter__(self) -> AsyncAgentCC:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        key = self._api_key
        key_preview = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        return f"AsyncAgentCC(base_url={self._base_url!r}, api_key={key_preview!r})"
