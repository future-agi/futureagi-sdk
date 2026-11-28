"""The no-egress helper clears every proxy variable a client library reads, in every case variant.

Each case sets one proxy variable to a CONNECT-aware loopback proxy sink, removes ``NO_PROXY``, runs the helper, and
sends one request carrying a planted marker key with ``requests`` (which reads the variables through ``urllib``, in
any case) to a loopback target, over https for an ``https_proxy`` variant. The sinks count connections and marker
bytes: the proxy sink must see none, and the target must see the connection (and the marker, over http).
"""

from __future__ import annotations

import os

import pytest
import requests

from tests.core import _egress
from tests.core._localhost_dial import KEY, Sink, proxy, target  # noqa: F401

PROXY_VARIABLES = (
    "HTTP_PROXY", "http_proxy", "Http_Proxy",
    "HTTPS_PROXY", "https_proxy", "Https_Proxy",
    "ALL_PROXY", "all_proxy", "All_Proxy",
)
CLEARED = {"http_proxy", "https_proxy", "all_proxy"}


@pytest.mark.parametrize("name", PROXY_VARIABLES)
def test_the_helper_clears_the_proxy_variable_and_the_request_goes_direct(name, tmp_path, target: Sink, proxy: Sink):
    patch = pytest.MonkeyPatch()
    try:
        for other in [k for k in os.environ if k.lower() in CLEARED | {"no_proxy"}]:
            patch.delenv(other)
        patch.setenv(name, f"http://127.0.0.1:{proxy.port}")
        _egress.install(patch, tmp_path)
        left = sorted(k for k in os.environ if k.lower() in CLEARED)
        scheme = "https" if name.lower() == "https_proxy" else "http"
        url = f"{scheme}://127.0.0.1:{target.port}/v1/traces"
        try:
            requests.get(url, headers={"X-Api-Key": KEY}, timeout=2)
        except requests.RequestException:
            pass
    finally:
        patch.undo()
    measured = {"left": left, "proxy": (proxy.connections, proxy.marker_bytes),
                "target": (target.connections, target.marker_bytes)}
    expected = {"left": [], "proxy": (0, 0), "target": (1, 0 if scheme == "https" else 1)}
    assert measured == expected, (proxy.first_lines, target.first_lines)
