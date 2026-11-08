"""Context-local session tracking with compact layered metadata headers."""

from __future__ import annotations

import contextvars
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fi.gateway._client import AgentCC, AsyncAgentCC


@dataclass
class Session:
    """Hierarchical workflow state and accumulated request accounting."""

    session_id: str = ""
    name: str | None = None
    path: str = "/"
    metadata: dict[str, Any] = field(default_factory=dict)
    _total_cost: float = field(default=0.0, init=False, repr=False)
    _request_count: int = field(default=0, init=False, repr=False)
    _total_tokens: int = field(default=0, init=False, repr=False)
    _steps: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.session_id:
            self.session_id = uuid.uuid4().hex

    def step(self, name: str) -> None:
        self._steps.append(name)
        self.path = f"/{name}" if self.path == "/" else f"{self.path}/{name}"

    def reset_path(self) -> None:
        self.path = "/"
        self._steps.clear()

    def to_headers(self) -> dict[str, str]:
        headers = {"x-agentcc-session-id": self.session_id}
        if self.name is not None:
            headers["x-agentcc-session-name"] = self.name
        if self.path != "/":
            headers["x-agentcc-session-path"] = self.path
        if self.metadata:
            headers["x-agentcc-metadata"] = json.dumps(self.metadata, separators=(",", ":"))
        return headers

    def track_request(self, cost: float = 0.0, tokens: int = 0) -> None:
        self._total_cost += cost
        self._total_tokens += tokens
        self._request_count += 1

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def total_tokens(self) -> int:
        return self._total_tokens


class SessionContext:
    """Bind a session to the current context; nested exits restore the parent."""

    def __init__(
        self, client: AgentCC | AsyncAgentCC, *, session_id: str | None = None,
        name: str | None = None, metadata: dict[str, Any] | None = None,
        path: str | None = None,
    ) -> None:
        self._client = client
        self._session = Session(session_id=session_id or "", name=name, metadata=metadata or {})
        if path:
            self._session.path = path if path.startswith("/") else f"/{path}"
        self._token: contextvars.Token[Any] | None = None

    def _dispatch(self, method: str, *args: Any) -> None:
        for callback in self._client._callbacks or []:
            fn = getattr(callback, method, None)
            if fn is not None:
                try:
                    fn(*args)
                except Exception:
                    logging.getLogger("fi.gateway").debug("Session callback raised", exc_info=True)

    def _enter(self) -> Session:
        self._token = self._client._session_var.set(self._session)
        self._dispatch("on_session_start", self._session)
        return self._session

    def _exit(self) -> None:
        if self._token is not None:
            try:
                self._dispatch(
                    "on_session_end", self._session, self._session.total_cost,
                    self._session.request_count, self._session.total_tokens,
                )
            finally:
                self._client._session_var.reset(self._token)
                self._token = None

    def __enter__(self) -> Session:
        return self._enter()

    def __exit__(self, *args: Any) -> None:
        self._exit()

    async def __aenter__(self) -> Session:
        return self._enter()

    async def __aexit__(self, *args: Any) -> None:
        self._exit()
