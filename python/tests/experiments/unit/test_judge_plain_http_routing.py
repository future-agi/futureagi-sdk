"""The experiments judge sends its key to a plain-http base URL directly: a proxy of the environment receives nothing."""

import asyncio
import types

import pytest

from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.test_header_key_senders import MARKER, proxied, remote, rig  # noqa: F401  (fixture)


def chat(base, monkeypatch):
    judge = Judge("is it right", model="m", base_url=base, timeout_s=3)
    ec = types.SimpleNamespace(usage=[])
    try:
        asyncio.run(judge._chat(ec, MARKER, "system", "user"))
    except Exception as error:  # noqa: BLE001 - the listener's reply is not a completion
        return error
    return None


def test_a_loopback_base_url_with_an_environment_proxy_is_sent_directly(rig, monkeypatch):
    proxied(rig, monkeypatch)
    chat(f"http://localhost:{rig.target.port}/v1", monkeypatch)
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0
    assert rig.target.marker_bytes > 0


def test_a_non_loopback_base_url_without_the_opt_in_sends_nothing(rig, monkeypatch):
    proxied(rig, monkeypatch)
    chat(f"{remote(rig.target)}/v1", monkeypatch)
    assert rig.connections() == 0 and rig.bytes() == 0


def test_the_opt_in_with_an_environment_proxy_is_sent_directly(rig, monkeypatch):
    proxied(rig, monkeypatch)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    chat(f"{remote(rig.target)}/v1", monkeypatch)
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0
    assert rig.target.marker_bytes > 0
