"""A refusal to send the keys reaches the caller with its own code.

The gateway clients, the knowledge-base client and the evaluation template registry report the same code as the shared
senders for the same situation: ``insecure_http_origin`` for a plain-http origin that is not loopback and has no opt-in,
``INSECURE_HTTP_REFUSED`` for a Future AGI host. Every host here is refused before a connection, and the resolver is
replaced by one that fails the test if it is asked.
"""

from __future__ import annotations

import asyncio
import socket

import httpx
import pytest

from fi.errors import ConfigurationError, InsecureHttpRefusedError
from tests._judged_mock_transport import JudgedMockTransport
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, Sink

SELF_HOSTED = "http://selfhosted.example.test:8080"
FUTURE_AGI = "http://api.futureagi.com"
REFUSALS = [(SELF_HOSTED, "insecure_http_origin", ConfigurationError),
            (FUTURE_AGI, "INSECURE_HTTP_REFUSED", InsecureHttpRefusedError)]


@pytest.fixture(autouse=True)
def no_dial(monkeypatch):
    for name in ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)

    def refuse(*args, **kwargs):
        raise AssertionError("a refused origin is not resolved")

    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def test_a_gateway_origin_without_the_opt_in_is_refused_with_its_code():
    from fi.gateway import AgentCCError
    from fi.gateway._http_security import validate_destination

    with pytest.raises(AgentCCError) as refused:
        validate_destination(SELF_HOSTED, SELF_HOSTED)
    assert refused.value.code == "insecure_http_origin"
    assert refused.value.get_error_code() == "insecure_http_origin"
    assert "FI_ALLOW_INSECURE_HTTP" in str(refused.value)


def test_a_gateway_future_agi_host_is_refused_with_its_code():
    from fi.gateway import AgentCCError
    from fi.gateway._http_security import validate_destination

    with pytest.raises(AgentCCError) as refused:
        validate_destination(FUTURE_AGI, FUTURE_AGI)
    assert refused.value.code == "INSECURE_HTTP_REFUSED"
    assert refused.value.get_error_code() == "INSECURE_HTTP_REFUSED"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_a_gateway_request_to_a_plain_origin_raises_the_typed_refusal(asynchronous):
    from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC

    sent = []

    def handle(request):
        sent.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    async def list_models():
        async with httpx.AsyncClient(transport=JudgedMockTransport(handle)) as http:
            async with AsyncAgentCC(api_key=MARKER_KEY, base_url=SELF_HOSTED, http_client=http) as client:
                await client.models.list()

    def list_models_blocking():
        with httpx.Client(transport=JudgedMockTransport(handle)) as http:
            with AgentCC(api_key=MARKER_KEY, base_url=SELF_HOSTED, http_client=http) as client:
                client.models.list()

    with pytest.raises(AgentCCError) as refused:
        asyncio.run(list_models()) if asynchronous else list_models_blocking()
    assert sent == []
    assert refused.value.get_error_code() == "insecure_http_origin"
    assert MARKER_KEY not in str(refused.value)


@pytest.mark.parametrize("base_url,code,error", REFUSALS)
def test_a_knowledge_base_name_does_not_hide_a_refusal(base_url, code, error):
    from fi.kb.client import KnowledgeBase

    with pytest.raises(error) as refused:
        KnowledgeBase(kb_name="docs", fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET, fi_base_url=base_url)
    assert refused.value.code == code
    assert "not found" not in str(refused.value)


def test_a_knowledge_base_that_the_server_does_not_have_is_not_found():
    from fi.kb.client import KnowledgeBase
    from fi.utils.errors import SDKException

    origin = Sink(status=b"404 Not Found")
    try:
        with pytest.raises(SDKException) as missing:
            KnowledgeBase(kb_name="docs", fi_api_key=MARKER_KEY, fi_secret_key=MARKER_SECRET,
                          fi_base_url=f"http://127.0.0.1:{origin.port}")
    finally:
        origin.close()
    assert "not found" in str(missing.value)
    assert not isinstance(missing.value, ConfigurationError)


@pytest.mark.parametrize("base_url,code,error", REFUSALS)
def test_the_eval_registry_raises_a_refusal(base_url, code, error):
    from fi.evals.core import cloud_registry

    cloud_registry._CACHE.clear()
    with pytest.raises(error) as refused:
        cloud_registry.load_registry(base_url, MARKER_KEY, MARKER_SECRET, force_refresh=True)
    assert refused.value.code == code
    assert MARKER_KEY not in str(refused.value) and MARKER_SECRET not in str(refused.value)
    assert cloud_registry._CACHE == {}
