"""The cloud eval registry fetch through a borrowed client asks that client about its own proxy.

A keyed HTTP fetch through the borrowed client's proxy is refused before connecting, even with
``FI_ALLOW_INSECURE_HTTP=1``. HTTPS connects through the proxy without sending it key bytes; with the opt-in,
an unproxied HTTP fetch sends the keys directly to the target. The sinks count connections and marker key bytes.
"""

from __future__ import annotations

import httpx
import pytest

from fi._keyed_errors import KeyedProxyRefusedError
from fi.evals._client_transport import _BorrowedSession
from fi.evals.core import cloud_registry
from tests.core._localhost_dial import KEY, SECRET, proxy, resolver_shim, target  # noqa: F401

OPT_IN = {"FI_ALLOW_INSECURE_HTTP": "1"}


def _load(client: httpx.Client, base_url: str):
    session = _BorrowedSession(lambda: client)
    try:
        return cloud_registry.load_registry(base_url, KEY, SECRET, session=session)
    finally:
        session.close()


def test_a_plain_http_keyed_fetch_through_the_borrowed_clients_proxy_is_refused(target, proxy):
    with resolver_shim(OPT_IN) as connects:
        with httpx.Client(proxy=f"http://127.0.0.1:{proxy.port}") as client:
            with pytest.raises(KeyedProxyRefusedError):
                _load(client, f"http://loop.test:{target.port}")
    assert (proxy.connections, proxy.marker_bytes) == (0, 0), proxy.first_lines
    assert (target.connections, target.marker_bytes) == (0, 0)
    assert connects == []


def test_an_https_fetch_through_the_borrowed_clients_proxy_carries_no_key_to_the_proxy(target, proxy):
    with resolver_shim(OPT_IN):
        with httpx.Client(proxy=f"http://127.0.0.1:{proxy.port}") as client:
            assert _load(client, f"https://loop.test:{target.port}") == {}
    assert proxy.connections == 1 and proxy.first_lines[0].startswith(b"CONNECT loop.test:"), proxy.first_lines
    assert proxy.marker_bytes == 0
    assert (target.connections, target.marker_bytes) == (0, 0)


def test_an_unproxied_borrowed_client_delivers_the_opted_in_plain_http_fetch(target, proxy):
    with resolver_shim(OPT_IN) as connects:
        with httpx.Client() as client:
            assert _load(client, f"http://loop.test:{target.port}") == {}
    assert target.connections == 1 and target.marker_bytes == 2, target.first_lines
    assert target.first_lines[0].startswith(b"GET /sdk/api/v1/get-evals/ ")
    assert (proxy.connections, proxy.marker_bytes) == (0, 0)
    assert connects == ["127.0.0.1"]
