"""``openai_kwargs()`` builds the arguments of an OpenAI client that the caller creates, and that client reads
``HTTP_PROXY``, ``HTTPS_PROXY`` and ``ALL_PROXY`` itself. A plain-http gateway URL that an environment proxy would route is
refused when the arguments are built (``KeyedProxyRefusedError``), as for every other sender, and the docstring says what
the function cannot decide. No host is resolved."""

from __future__ import annotations

import socket

import pytest

from fi.errors import ConfigurationError
from fi.gateway import AgentCCError, openai_kwargs

KEY = "fi-gw-marker-key-1f6b"
NAMES = ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy",
         "NO_PROXY", "no_proxy", "FI_GATEWAY_API_KEY", "FI_GATEWAY_BASE_URL", "AGENTCC_API_KEY", "AGENTCC_BASE_URL")


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)

    def refuse(*args, **kwargs):
        raise AssertionError("the arguments are built without resolving a host")

    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def test_an_https_gateway_with_a_proxy_environment_is_built(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:9")
    assert openai_kwargs(api_key=KEY, base_url="https://gateway.example.test")["base_url"] == "https://gateway.example.test/v1"


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"])
def test_a_plain_http_gateway_with_the_opt_in_and_a_proxy_environment_is_refused(monkeypatch, variable):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    monkeypatch.setenv(variable, "http://127.0.0.1:9")
    with pytest.raises(ConfigurationError) as refused:
        openai_kwargs(api_key=KEY, base_url="http://selfhosted.example.test:8080")
    assert refused.value.code == "KEYED_PROXY_REFUSED" and refused.value.get_error_code() == "KEYED_PROXY_REFUSED"
    assert KEY not in str(refused.value)


def test_a_plain_http_gateway_with_the_opt_in_and_no_proxy_is_built(monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    kwargs = openai_kwargs(api_key=KEY, base_url="http://selfhosted.example.test:8080")
    assert kwargs["base_url"] == "http://selfhosted.example.test:8080/v1" and kwargs["api_key"] == KEY


def test_a_plain_http_gateway_with_the_opt_in_and_the_host_in_no_proxy_is_built(monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "selfhosted.example.test")
    assert openai_kwargs(api_key=KEY, base_url="http://selfhosted.example.test:8080")["api_key"] == KEY


def test_a_plain_http_gateway_without_the_opt_in_keeps_its_own_refusal(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    with pytest.raises(AgentCCError) as refused:
        openai_kwargs(api_key=KEY, base_url="http://selfhosted.example.test:8080")
    assert refused.value.code == "insecure_http_origin"


def test_the_docstring_says_the_callers_client_reads_the_proxy_variables():
    doc = openai_kwargs.__doc__ or ""
    assert "HTTP_PROXY" in doc and "proxy" in doc.lower()


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
def test_a_loopback_plain_http_gateway_that_a_proxy_environment_routes_is_refused(monkeypatch, variable):
    monkeypatch.setenv(variable, "http://127.0.0.1:9")
    with pytest.raises(ConfigurationError) as refused:
        openai_kwargs(api_key=KEY, base_url="http://127.0.0.1:8080")
    assert refused.value.code == "KEYED_PROXY_REFUSED"


def test_a_loopback_plain_http_gateway_named_in_no_proxy_is_built(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    assert openai_kwargs(api_key=KEY, base_url="http://127.0.0.1:8080")["base_url"] == "http://127.0.0.1:8080/v1"
    assert openai_kwargs(api_key=KEY, base_url="http://localhost:8080")["base_url"] == "http://localhost:8080/v1"


def test_a_loopback_plain_http_gateway_without_a_proxy_environment_is_built():
    assert openai_kwargs(api_key=KEY, base_url="http://127.0.0.1:8080")["api_key"] == KEY


def test_an_ipv6_loopback_plain_http_gateway_named_in_no_proxy_is_built(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1,::1")
    assert openai_kwargs(api_key=KEY, base_url="http://[::1]:8080")["base_url"] == "http://[::1]:8080/v1"


def test_the_refusal_names_only_the_remedies_the_function_offers(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    with pytest.raises(ConfigurationError) as refused:
        openai_kwargs(api_key=KEY, base_url="http://127.0.0.1:8080")
    assert "http_client" not in str(refused.value) and "http_client" not in (openai_kwargs.__doc__ or "")
