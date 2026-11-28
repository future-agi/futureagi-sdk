"""A plain-http base URL whose host is written with a percent-encoded character is refused by every sender of the API
keys, whatever ``FI_ALLOW_INSECURE_HTTP`` says: the sending libraries decode the host, so a name written
``api.%66utureagi.com`` is the Future AGI host ``api.futureagi.com``. Every row is measured at a loopback listener
(the target) and a proxy sink: no connection and no marker byte. Names resolve to this machine through a resolver shim;
no real host is contacted."""

from __future__ import annotations

import os
from typing import Any
from unittest import mock

import pytest

from fi.errors import ConfigurationError
from fi.gateway._exceptions import AgentCCError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_plain_http_opt_in_per_sender import NAMES, SENDERS
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)

ENCODED_HOSTS = [
    "api.%66utureagi.com",
    "%61pi.%66%75tureagi.%63om",
    "api%2efutureagi.com",
    "api%2Efutureagi%2ecom",
    "api.futureagi.c%6Fm",
    "api.futureagi.c%6fm",
    "census-host.%74est",
]
FLAGS = [None, "1", "true", "0"]


def _attempt(sinks_: dict, name: str, host: str, flag: Any) -> tuple[str, Any]:
    for each in sinks_.values():
        each.reset()
    base = f"http://{host}:{sinks_['target'].port}"
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**clean, **({} if flag is None else {"FI_ALLOW_INSECURE_HTTP": flag})}, clear=True):
        try:
            SENDERS[name][0](base)
        except Exception as error:
            return "failed", error
    return "sent", None


@pytest.mark.parametrize("flag", FLAGS)
@pytest.mark.parametrize("host", ENCODED_HOSTS)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_sends_no_byte_to_a_percent_encoded_plain_http_host(sinks, resolver, name, host, flag):
    outcome, error = _attempt(sinks, name, host, flag)
    for each in sinks.values():
        assert each.marker_bytes == 0 and each.requests == 0, [bytes(c)[:80] for c in each.chunks]
    assert outcome == "failed"
    if not SENDERS[name][1]:
        assert isinstance(error, (ConfigurationError, AgentCCError)), repr(error)
    assert MARKER_KEY not in str(error) and MARKER_SECRET not in str(error)
