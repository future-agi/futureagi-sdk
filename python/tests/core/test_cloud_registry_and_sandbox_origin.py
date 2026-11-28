"""Two senders of the Future AGI keys: the evaluation template registry does not follow a redirect (the target receives no
request and the marker keys reach the configured host only), and the sandbox base URL read from ``OMEGA_BASE_URL`` is judged
on the host as written, so an address written with ideographic, fullwidth or halfwidth full stops is a name and is refused."""

from __future__ import annotations

import logging

import pytest

from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, Sink


def test_the_eval_registry_does_not_follow_a_redirect_with_keys(caplog):
    from fi.evals.core import cloud_registry

    other = Sink()
    origin = Sink(status=b"302 Found", location=f"http://127.0.0.1:{other.port}/landing")
    cloud_registry._CACHE.clear()
    try:
        with caplog.at_level(logging.WARNING):
            registry = cloud_registry.load_registry(f"http://127.0.0.1:{origin.port}", MARKER_KEY, MARKER_SECRET, force_refresh=True)
        assert registry == {}
        assert origin.requests == 1 and other.requests == 0
        assert other.marker_bytes == 0
        assert "KeyedRedirectRefusedError" in caplog.text
        assert MARKER_KEY not in caplog.text and MARKER_SECRET not in caplog.text
    finally:
        origin.close()
        other.close()


@pytest.mark.parametrize("dot", ["。", "．", "｡"])
def test_a_sandbox_base_url_with_a_non_ascii_dot_host_is_refused(dot):
    from fi.sandbox._connection import resolve_origin

    host = dot.join(["127", "0", "0", "1"])
    env = {"OMEGA_BASE_URL": f"http://{host}:81", "FI_API_KEY": MARKER_KEY, "FI_SECRET_KEY": MARKER_SECRET}
    with pytest.raises(ConfigurationError) as info:
        resolve_origin(env)
    assert MARKER_KEY not in str(info.value)


def test_a_sandbox_base_url_with_an_ascii_loopback_host_is_accepted():
    from fi.sandbox._connection import resolve_origin

    origin = resolve_origin({"OMEGA_BASE_URL": "http://127.0.0.1:81", "FI_API_KEY": MARKER_KEY, "FI_SECRET_KEY": MARKER_SECRET})
    assert origin.url.host == "127.0.0.1"
