"""The gateway's httpx clients with loopback sent straight to this machine.

Clients send plain HTTP and loopback requests over their direct transport. They use
:func:`fi._core.loopback.is_loopback_host` to identify loopback. For other requests, httpx uses ``HTTP_PROXY``,
``HTTPS_PROXY``, ``ALL_PROXY`` and ``NO_PROXY`` to select the transport. httpx configures limits, timeouts and proxy
transports. For the corresponding platform routing rules, see ``fi._core.transport``.
"""

from __future__ import annotations

from typing import Any

import httpx

from fi._core.loopback import is_loopback_host, pin_localhost


class LoopbackDirectClient(httpx.Client):
    """``httpx.Client`` whose plain-http and loopback requests skip an environment proxy, and whose direct connections
    dial the name ``localhost`` to 127.0.0.1, then ``::1``."""

    def _init_transport(self, *args: Any, **kwargs: Any) -> httpx.BaseTransport:
        return pin_localhost(super()._init_transport(*args, **kwargs))

    def _transport_for_url(self, url: httpx.URL) -> httpx.BaseTransport:
        if url.scheme == "http" or is_loopback_host(url.host):
            return self._transport
        return super()._transport_for_url(url)


class AsyncLoopbackDirectClient(httpx.AsyncClient):
    """``httpx.AsyncClient`` whose plain-http and loopback requests skip an environment proxy, and whose direct
    connections dial the name ``localhost`` to 127.0.0.1, then ``::1``."""

    def _init_transport(self, *args: Any, **kwargs: Any) -> httpx.AsyncBaseTransport:
        return pin_localhost(super()._init_transport(*args, **kwargs))

    def _transport_for_url(self, url: httpx.URL) -> httpx.AsyncBaseTransport:
        if url.scheme == "http" or is_loopback_host(url.host):
            return self._transport
        return super()._transport_for_url(url)
