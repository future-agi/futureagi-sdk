"""A plain-http base URL whose host is written with the ideographic (``。``), fullwidth (``．``) or halfwidth (``｡``) full
stop is a name as written, not an address in 127.0.0.0/8, although the sending libraries read each of those as a dot and
connect to ``127.0.0.1``. Every sender of the API keys refuses it before a connection, loopback listener included, unless
``FI_ALLOW_INSECURE_HTTP`` is exactly ``1``. Each row is measured at the listener the library would reach (the target)
and at two proxy sinks: no connection and no marker byte. Nothing leaves this machine."""

from __future__ import annotations

import os
from typing import Any
from unittest import mock

import pytest

from fi.errors import ConfigurationError, PlatformNotConfiguredError
from fi.gateway._exceptions import AgentCCError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_plain_http_opt_in_per_sender import NAMES, SENDERS
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)

DOTTED = ["127。0。0。1", "127．0．0．1", "127｡0｡0｡1", "127.0.0。1", "127．0.0.1"]
SANDBOX = {"sandbox list", "async sandbox list", "sandbox file download", "async sandbox file download"}
OTHER_VALUES = ["true", "yes", "0", "", " 1", "01"]


def _attempt(sinks_: dict, name: str, host: str, env: dict[str, str]) -> tuple[str, Any]:
    for each in sinks_.values():
        each.reset()
    base = f"http://{host}:{sinks_['target'].port}"
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**clean, **env}, clear=True):
        try:
            SENDERS[name][0](base)
        except Exception as error:  # noqa: BLE001 - the kind of failure is what the tests read
            return "failed", error
    return "sent", None


def _nothing_reached_a_listener(sinks_: dict) -> None:
    for each in sinks_.values():
        assert each.marker_bytes == 0 and each.requests == 0, [bytes(c)[:80] for c in each.chunks]


@pytest.mark.parametrize("host", DOTTED)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_refuses_a_non_ascii_dot_host_without_the_opt_in(sinks, resolver, name, host):
    outcome, error = _attempt(sinks, name, host, {})
    _nothing_reached_a_listener(sinks)
    assert outcome == "failed"
    if not SENDERS[name][1]:
        assert isinstance(error, (ConfigurationError, AgentCCError)), repr(error)
    assert MARKER_KEY not in str(error) and MARKER_SECRET not in str(error)
    if name not in SANDBOX and not SENDERS[name][1]:
        if isinstance(error, PlatformNotConfiguredError):  # the platform origin has a code of its own
            assert error.code == "invalid_platform_url"
        else:
            assert error.code == "insecure_http_origin" and error.get_error_code() == "insecure_http_origin", repr(error)


@pytest.mark.parametrize("value", OTHER_VALUES)
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_refuses_a_non_ascii_dot_host_when_the_opt_in_is_not_exactly_one(sinks, resolver, name, value):
    outcome, error = _attempt(sinks, name, DOTTED[0], {"FI_ALLOW_INSECURE_HTTP": value})
    _nothing_reached_a_listener(sinks)
    assert outcome == "failed"


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
@pytest.mark.parametrize("name", NAMES)
def test_a_sender_sends_nothing_to_a_proxy_for_a_non_ascii_dot_host(sinks, resolver, name, variable):
    proxy = f"http://127.0.0.1:{sinks['sinkA'].port}"
    outcome, _ = _attempt(sinks, name, DOTTED[1], {variable: proxy})
    _nothing_reached_a_listener(sinks)
    assert outcome == "failed"
