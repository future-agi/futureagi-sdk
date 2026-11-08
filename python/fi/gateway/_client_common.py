"""Pieces both clients share: lazily built resource properties and the cost ledger."""

from __future__ import annotations

import importlib
import threading
from typing import Any


def resource_property(attr: str, module: str, cls_name: str) -> property:
    """A read-only property that builds ``module.cls_name(client)`` on first use.

    The instance is cached on ``attr`` and built under the client's lock, so two
    threads reading ``client.chat`` at once get the same object.
    """

    def get(self: Any) -> Any:
        if attr in {"_batches", "_moderations"}:
            import warnings

            warnings.warn(
                f"client.{attr[1:]} is a deprecated released compatibility resource.",
                DeprecationWarning, stacklevel=2,
            )
        value = getattr(self, attr)
        if value is None:
            with self._lock:
                value = getattr(self, attr)
                if value is None:
                    value = getattr(importlib.import_module(module), cls_name)(self)
                    setattr(self, attr, value)
        return value

    get.__name__ = attr.lstrip("_")
    get.__qualname__ = get.__name__
    return property(get)


class ClientState:
    """Released mutable redaction option and context-local active sessions."""

    def _init_audio_upload_mode(self, mode: str) -> None:
        if mode not in {"published", "normalized"}:
            raise ValueError("audio_upload_mode must be 'published' or 'normalized'")
        self._audio_upload_mode = mode

    def _init_metadata_mode(self, mode: str) -> None:
        """Only explicit merge mode layers client, session and request metadata."""
        if mode not in {"replace", "merge"}:
            raise ValueError("metadata_mode must be 'replace' or 'merge'")
        self._metadata_mode = mode

    def _init_callback_options(self, mode: str, expanded: bool) -> None:
        """Published descriptors by default; snapshots and extra events are opt-in."""
        if mode not in {"published", "snapshot"}:
            raise ValueError("callback_mode must be 'published' or 'snapshot'")
        self._callback_mode = mode
        self._expanded_callback_events = expanded

    def _init_compat(self, redact_messages: bool, pre_call_rules: Any, modify_params: bool) -> None:
        import contextvars
        self._session_var = contextvars.ContextVar(f"gateway_session_{id(self)}", default=None)
        self._warned_http_origins: set[tuple[str, str, int]] = set()
        self._http_warning_lock = threading.Lock()
        self._redact_messages = redact_messages
        self._pre_call_rules = pre_call_rules
        self._modify_params = modify_params

    @property
    def _active_session(self) -> Any:
        return self._session_var.get()

    @_active_session.setter
    def _active_session(self, session: Any) -> None:
        self._session_var.set(session)

    @property
    def redact_messages(self) -> bool:
        return self._redact_messages

    @redact_messages.setter
    def redact_messages(self, value: bool) -> None:
        import warnings

        warnings.warn("redact_messages is a deprecated compatibility option.", DeprecationWarning, stacklevel=2)
        self._redact_messages = value
        base = getattr(self, "_base_client", None)
        if base is not None:
            base._redact_messages = value


class CostLedger:
    """The running total of ``x-agentcc-cost`` across a client's responses (D-15).

    A client and every ``with_options()`` copy of it share one ledger, as they share
    one connection pool. agentcc 1.x kept a counter nobody added to, so
    ``current_cost`` was always 0.0.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total = 0.0

    @property
    def total(self) -> float:
        return self._total

    def add(self, cost: float) -> None:
        with self._lock:
            self._total += cost

    def reset(self) -> None:
        with self._lock:
            self._total = 0.0


def derived_options(
    client: Any,
    *,
    timeout: Any,
    max_retries: Any,
    extra_headers: dict[str, str] | None,
    extra_query: dict[str, str] | None,
    session_id: Any,
    metadata: Any,
    trace_id: Any,
    drop_params: Any,
) -> dict[str, Any]:
    """The constructor arguments of ``client.with_options(...)``'s new client.

    Every option not overridden is carried over, ``retry_policy`` included, and
    ``trace_id`` becomes the copy's default ``x-agentcc-trace-id`` header (a
    per-request ``trace_id=`` still wins). agentcc 1.x dropped both (D-15).
    """
    from fi.gateway._constants import HEADER_TRACE_ID, NOT_GIVEN

    def pick(value: Any, current: Any) -> Any:
        return current if value is NOT_GIVEN else value

    headers = dict(client._default_headers or {})
    headers.update(extra_headers or {})
    if trace_id is not NOT_GIVEN and trace_id is not None:
        headers[HEADER_TRACE_ID] = str(trace_id)
    query = dict(client._default_query or {})
    query.update(extra_query or {})
    return {
        "api_key": client._api_key,
        "base_url": client._base_url,
        "timeout": pick(timeout, client._timeout),
        "max_retries": pick(max_retries, client._max_retries),
        "default_headers": headers or None,
        "default_query": query or None,
        "session_id": pick(session_id, client._session_id),
        "metadata": pick(metadata, client._metadata),
        "metadata_mode": client._metadata_mode,
        "audio_upload_mode": client._audio_upload_mode,
        "config": client._config,
        "callbacks": client._callbacks,
        "callback_mode": client._callback_mode,
        "expanded_callback_events": client._expanded_callback_events,
        "http_client": client._http_client,
        "drop_params": pick(drop_params, client._drop_params),
        "retry_policy": client._retry_policy,
        "redact_messages": client._redact_messages,
        "pre_call_rules": client._pre_call_rules,
        "modify_params": client._modify_params,
        "enable_json_schema_validation": client._enable_json_schema_validation,
    }
