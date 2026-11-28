"""The evaluation template registry sends its keyed request plain-http direct, whatever the proxy variables say: for a
loopback host and for a host that is not loopback and opted into, the keys reach the registry host and not the proxy."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
@pytest.mark.parametrize("host", ["127.0.0.1", "registry-host.test"])
def test_the_registry_request_is_sent_direct(sinks, resolver, host, variable):
    from fi.evals.core import cloud_registry

    for each in sinks.values():
        each.reset()
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    env = {**clean, "FI_ALLOW_INSECURE_HTTP": "1", variable: f"http://127.0.0.1:{sinks['sinkA'].port}"}
    with mock.patch.dict(os.environ, env, clear=True):
        cloud_registry._CACHE.clear()
        cloud_registry.load_registry(f"http://{host}:{sinks['target'].port}", MARKER_KEY, MARKER_SECRET, force_refresh=True)
    assert sinks["target"].marker_bytes > 0
    assert sinks["sinkA"].marker_bytes == 0 and sinks["sinkA"].requests == 0
