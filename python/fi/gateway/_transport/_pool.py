"""The httpx client a client and its ``with_options()`` copies send through."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class HttpPool:
    """One httpx client, so one connection pool, for a client and every copy of it.

    Each ``AgentCC`` / ``AsyncAgentCC`` builds its own transport from its own options
    (timeout, retries, headers, session, metadata), and every transport sends through
    the pool of the client it was copied from. agentcc 1.x shared the parent's
    transport instead, so a copy made after the parent's first request kept the
    parent's options, and a copy made before it shared nothing (D-15). Sharing the
    httpx client is safe because every send passes its own ``timeout=``; the pooled
    client's default timeout is never used.

    A client passed as ``http_client=`` is used as given and never closed here.
    Without one, the first transport to send builds the client (under a lock, so two
    threads build one), and :meth:`close` / :meth:`aclose` close it; the next send
    after that builds a new one.
    """

    def __init__(self, http_client: Any = None) -> None:
        self._lock = threading.Lock()
        self.client: Any = http_client
        self.owned = http_client is None

    def get(self, build: Callable[[], Any]) -> Any:
        """The pooled client, built by *build* if there is none yet."""
        client = self.client
        if client is None:
            with self._lock:
                if self.client is None:
                    self.client = build()
                client = self.client
        return client

    def _release(self) -> Any:
        with self._lock:
            client = self.client if self.owned else None
            if client is not None:
                self.client = None
            return client

    def close(self) -> None:
        """Close the client this pool built (a sync ``httpx.Client``), if any."""
        client = self._release()
        if client is not None:
            client.close()

    async def aclose(self) -> None:
        """Close the client this pool built (an ``httpx.AsyncClient``), if any."""
        client = self._release()
        if client is not None:
            await client.aclose()
