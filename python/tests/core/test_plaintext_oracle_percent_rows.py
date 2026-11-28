"""Rows the sealed plain-HTTP oracle does not carry: a host written with a percent-encoded character. The oracle's own
rows are matched in test_plaintext_oracle_conformance; these are driven the same way (``_send``, the SDK's own key-carrying
httpx request) and refused for every opt-in value and caller, with no marker byte and no connection at any sink. A TLS
URL with the same host is not judged here."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from fi._core.http_security import plaintext_decision
from tests.core._plaintext_oracle import CALLERS, PROXY_NAMES, _send
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)

HOSTS = [
    "api.%66utureagi.com",
    "%61pi.%66%75tureagi.%63om",
    "api%2efutureagi.com",
    "api%2Efutureagi.com",
    "census-host.%74est",
]


@pytest.mark.parametrize("value", [None, "1", "true", "0"])
@pytest.mark.parametrize("caller", sorted(CALLERS))
@pytest.mark.parametrize("host", HOSTS)
def test_a_percent_encoded_plain_http_host_is_refused_with_no_byte_at_any_sink(sinks, host, caller, value):
    for each in sinks.values():
        each.reset()
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    env = {**clean, **({} if value is None else {"FI_ALLOW_INSECURE_HTTP": value})}
    with mock.patch.dict(os.environ, env, clear=True):
        outcome = _send(f"http://{host}:{sinks['target'].port}/", caller, sinks)
    assert outcome.startswith("refused:"), outcome
    assert all(each.marker_bytes == 0 and each.requests == 0 for each in sinks.values())


@pytest.mark.parametrize("host", HOSTS)
def test_the_decision_for_a_percent_encoded_plain_http_host_is_ambiguous_host(host):
    assert plaintext_decision(f"http://{host}/", allow_insecure_http=True).reason == "ambiguous_host"


@pytest.mark.parametrize("host", ["api.%66utureagi.com", "census-host.%74est"])
def test_the_same_host_over_tls_is_not_refused_as_a_plain_http_host(host):
    assert plaintext_decision(f"https://{host}/").allowed
