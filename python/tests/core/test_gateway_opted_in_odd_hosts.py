"""With ``FI_ALLOW_INSECURE_HTTP=1`` a gateway base URL whose host is written with non-ASCII dots, or that the HTTP library
cannot read (a stray backslash or control character), is refused with the code ``insecure_http_origin`` by the clients and
by the helpers (``check_valid_key`` is ``False``, ``health_check`` is the error status), and nothing reaches the listener."""

from __future__ import annotations

import os
from unittest import mock

import pytest

from fi.errors import ConfigurationError
from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from fi.gateway._http_security import validate_destination
from fi.gateway._utils import check_valid_key, health_check
from tests.core._plaintext_oracle import MARKER_KEY, PROXY_NAMES, Sink


@pytest.fixture(scope="module")
def target():
    sink = Sink()
    yield sink
    sink.close()


def _forms(port: int) -> dict[str, str]:
    return {
        "ideographic full stop": f"http://127。0。0。1:{port}",
        "fullwidth full stop": f"http://127．0．0．1:{port}",
        "halfwidth ideographic full stop": f"http://127｡0｡0｡1:{port}",
        "backslash after the port": f"http://127.0.0.1:{port}\\x",
        "control character in the path": f"http://127.0.0.1:{port}/a\x01b",
    }


NAMES = list(_forms(1))


def _env() -> mock.patch.dict:
    env = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    env["FI_ALLOW_INSECURE_HTTP"] = "1"
    return mock.patch.dict(os.environ, env, clear=True)


def _assert_coded(error: BaseException) -> None:
    assert getattr(error, "code", None) == "insecure_http_origin", repr(error)
    assert isinstance(error, AgentCCError) and isinstance(error, ConfigurationError)
    assert MARKER_KEY not in f"{error} {error!r}"


@pytest.mark.parametrize("name", NAMES)
def test_validate_destination_refuses_with_the_code(target, name):
    base = _forms(target.port)[name]
    with _env(), pytest.raises(AgentCCError) as refused:
        validate_destination(base, base)
    _assert_coded(refused.value)


@pytest.mark.parametrize("name", NAMES)
def test_the_sync_client_refuses_with_the_code(target, name):
    target.reset()
    with _env(), pytest.raises(AgentCCError) as refused:
        client = AgentCC(api_key=MARKER_KEY, base_url=_forms(target.port)[name], max_retries=0)
        try:
            client.models.list()
        finally:
            client.close()
    _assert_coded(refused.value)
    assert target.marker_bytes == 0 and target.requests == 0


@pytest.mark.parametrize("name", NAMES)
def test_the_async_client_refuses_with_the_code(target, name):
    import asyncio

    async def go() -> None:
        client = AsyncAgentCC(api_key=MARKER_KEY, base_url=_forms(target.port)[name], max_retries=0)
        try:
            await client.models.list()
        finally:
            await client.aclose()

    target.reset()
    with _env(), pytest.raises(AgentCCError) as refused:
        asyncio.run(go())
    _assert_coded(refused.value)
    assert target.marker_bytes == 0 and target.requests == 0


@pytest.mark.parametrize("name", NAMES)
def test_the_helpers_refuse_and_send_nothing(target, name):
    target.reset()
    base = _forms(target.port)[name]
    with _env():
        assert check_valid_key(MARKER_KEY, base) is False
        assert health_check(api_key=MARKER_KEY, base_url=base)["status"] == "error"
        assert health_check("m", api_key=MARKER_KEY, base_url=base)["status"] == "error"
    assert target.marker_bytes == 0 and target.requests == 0, [bytes(c)[:80] for c in target.chunks]
