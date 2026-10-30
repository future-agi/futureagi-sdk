"""Session tracking and context management for the AgentCC SDK."""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fi.gateway._client import AsyncAgentCC, AgentCC


@dataclass
class Session:
    """Manages session state across multiple requests.

    Tracks a hierarchical path through a workflow, accumulates cost and token
    counts, and converts its state into HTTP headers sent to the gateway.

    Args:
        session_id: Unique identifier. Auto-generated UUID if not provided.
        name: Optional human-readable label for the session.
        path: Hierarchical path, starts at ``/``.
        metadata: Arbitrary key-value metadata to include in requests.
    """

    session_id: str = ""
    name: str | None = None
    path: str = "/"
    metadata: dict[str, Any] = field(default_factory=dict)

    # Internal tracking (not part of __init__)
    _total_cost: float = field(default=0.0, init=False, repr=False)
    _request_count: int = field(default=0, init=False, repr=False)
    _total_tokens: int = field(default=0, init=False, repr=False)
    _steps: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.session_id:
            self.session_id = uuid.uuid4().hex

    def step(self, name: str) -> None:
        """Push a step onto the path.

        If the current path is ``/research``, calling ``step("summarize")``
        makes it ``/research/summarize``.
        """
        self._steps.append(name)
        if self.path == "/":
            self.path = f"/{name}"
        else:
            self.path = f"{self.path}/{name}"

    def reset_path(self) -> None:
        """Reset the path back to ``/`` and clear all steps."""
        self.path = "/"
        self._steps.clear()

    def to_headers(self) -> dict[str, str]:
        """Convert session state to HTTP headers.

        Returns:
            Dict of headers to merge into outgoing requests:
            - ``x-agentcc-session-id``
            - ``x-agentcc-session-name`` (if set)
            - ``x-agentcc-session-path`` (if not ``/``)
            - ``x-agentcc-metadata-{key}`` for each metadata entry
        """
        headers: dict[str, str] = {
            "x-agentcc-session-id": self.session_id,
        }
        if self.name is not None:
            headers["x-agentcc-session-name"] = self.name
        if self.path != "/":
            headers["x-agentcc-session-path"] = self.path
        for key, value in self.metadata.items():
            headers[f"x-agentcc-metadata-{key}"] = str(value)
        return headers

    def track_request(self, cost: float = 0.0, tokens: int = 0) -> None:
        """Update internal counters after a completed request.

        Args:
            cost: Cost of the request in dollars.
            tokens: Number of tokens consumed.
        """
        self._total_cost += cost
        self._total_tokens += tokens
        self._request_count += 1

    @property
    def total_cost(self) -> float:
        """Cumulative cost across all tracked requests."""
        return self._total_cost

    @property
    def request_count(self) -> int:
        """Number of tracked requests."""
        return self._request_count

    @property
    def total_tokens(self) -> int:
        """Cumulative token count across all tracked requests."""
        return self._total_tokens


class SessionContext:
    """Context manager that binds a :class:`Session` to a client.

    While entered, the session is the client's ``_active_session`` for the current thread or
    asyncio task only; exiting restores whatever was active before (an outer session, or none).
    Supports both sync (``with``) and async (``async with``) usage.

    Usage::

        with client.session(name="research") as sess:
            sess.step("search")
            client.chat.completions.create(...)  # session headers auto-attached
    """

    def __init__(
        self,
        client: AgentCC | AsyncAgentCC,
        *,
        session_id: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        self._session = Session(
            session_id=session_id or "",
            name=name,
            metadata=metadata or {},
        )
        self._token: contextvars.Token[Any] | None = None

    # The client's active session is a ContextVar, so two threads or asyncio tasks sharing one
    # client each see the session they entered, and leaving a nested session restores the outer one.

    def _enter(self) -> Session:
        self._token = self._client._session_var.set(self._session)  # type: ignore[attr-defined]
        return self._session

    def _exit(self) -> None:
        if self._token is not None:
            self._client._session_var.reset(self._token)  # type: ignore[attr-defined]
            self._token = None

    # --- Sync context manager ---

    def __enter__(self) -> Session:
        return self._enter()

    def __exit__(self, *args: Any) -> None:
        self._exit()

    # --- Async context manager ---

    async def __aenter__(self) -> Session:
        return self._enter()

    async def __aexit__(self, *args: Any) -> None:
        self._exit()
