"""openai_kwargs(): arguments for a stock OpenAI SDK pointed at the gateway.

The result always holds an explicit ``api_key``: the OpenAI SDK falls back to
``OPENAI_API_KEY`` when none is passed, which would send the user's OpenAI key to the
gateway (critique B1). It resolves the key and base URL exactly as ``AgentCC`` does
(``FI_GATEWAY_*``, then ``AGENTCC_*``; the FI key pair refused; no hosted default), and
``import fi.gateway`` never imports ``openai``. Also here: the other names fi.gateway adds
to agentcc 1.0's surface (``AgentCCDeprecationWarning``, ``AgentCCMetadata`` and
``RateLimitInfo`` at the top level).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import httpx
import pytest

import fi
import fi.gateway as gw
from fi.gateway import AgentCCError, CacheConfig, GatewayConfig, openai_kwargs

GW = "http://127.0.0.1:8090"
ALL_PREFIXES = ("AGENTCC_", "FI_", "OPENAI_")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(ALL_PREFIXES):
            monkeypatch.delenv(name)


def test_the_three_arguments_with_an_explicit_key_and_the_v1_base(monkeypatch) -> None:
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "gw-key")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", GW)
    assert openai_kwargs() == {
        "api_key": "gw-key",
        "base_url": f"{GW}/v1",
        "default_headers": {},
    }


@pytest.mark.parametrize(
    "given",
    [GW, f"{GW}/", f"{GW}/v1", f"{GW}/v1/", "http://127.0.0.1:8090//v1//"],
)
def test_the_base_url_is_the_origin_plus_one_v1(given: str) -> None:
    assert openai_kwargs(api_key="k", base_url=given)["base_url"] == f"{GW}/v1"


def test_a_path_prefix_is_kept() -> None:
    assert (
        openai_kwargs(api_key="k", base_url="https://h.example/gw/v1")["base_url"]
        == "https://h.example/gw/v1"
    )


def test_arguments_win_over_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "env-key")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", "http://env.example")
    out = openai_kwargs(api_key="arg-key", base_url=GW)
    assert (out["api_key"], out["base_url"]) == ("arg-key", f"{GW}/v1")


def test_the_agentcc_names_are_still_read(monkeypatch) -> None:
    monkeypatch.setenv("AGENTCC_API_KEY", "old-key")
    monkeypatch.setenv("AGENTCC_BASE_URL", GW)
    out = openai_kwargs()
    assert (out["api_key"], out["base_url"]) == ("old-key", f"{GW}/v1")


def test_no_key_raises_even_with_openai_api_key_set(monkeypatch) -> None:
    """Without this, OpenAI(**openai_kwargs()) would read OPENAI_API_KEY and send it."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", GW)
    with pytest.raises(AgentCCError) as err:
        openai_kwargs()
    assert "FI_GATEWAY_API_KEY" in str(err.value)
    assert "sk-openai-secret" not in str(err.value)


def test_no_base_url_raises_and_openai_base_url_is_not_read(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.example/v1")
    with pytest.raises(AgentCCError) as err:
        openai_kwargs(api_key="k")
    assert "FI_GATEWAY_BASE_URL" in str(err.value)


@pytest.mark.parametrize("name", ["FI_API_KEY", "FI_SECRET_KEY"])
def test_the_fi_key_pair_is_refused(monkeypatch, name: str) -> None:
    monkeypatch.setenv(name, "fi-pair-value-0123456789")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", GW)
    with pytest.raises(AgentCCError) as err:
        openai_kwargs(api_key="fi-pair-value-0123456789")
    assert name in str(err.value)
    assert "fi-pair-value-0123456789" not in str(err.value)


def test_with_every_fi_and_openai_variable_set_only_gateway_values_come_out(
    monkeypatch,
) -> None:
    for name, value in {
        "FI_API_KEY": "fi-key",
        "FI_SECRET_KEY": "fi-secret",
        "FI_BASE_URL": "http://fi.example",
        "FI_PLATFORM_TOKEN": "fi-token",
        "FI_WORKSPACE_ID": "ws",
        "OPENAI_API_KEY": "sk-openai",
        "OPENAI_ORG_ID": "org-1",
        "OPENAI_PROJECT_ID": "proj-1",
        "OPENAI_BASE_URL": "https://api.openai.example/v1",
        "FI_GATEWAY_API_KEY": "gw-key",
        "FI_GATEWAY_BASE_URL": GW,
    }.items():
        monkeypatch.setenv(name, value)
    out = openai_kwargs(session_id="s1")
    assert out == {
        "api_key": "gw-key",
        "base_url": f"{GW}/v1",
        "default_headers": {"x-agentcc-session-id": "s1"},
    }
    text = json.dumps(out)
    for leaked in ("fi-key", "fi-secret", "fi-token", "sk-openai", "org-1", "proj-1"):
        assert leaked not in text


def test_gateway_parameters_become_the_create_headers_set() -> None:
    out = openai_kwargs(
        api_key="k",
        base_url=GW,
        config=GatewayConfig(cache=CacheConfig(ttl=300)),
        trace_id="t",
        session_id="s",
        session_name="flow",
        session_path="/a/b",
        metadata={"team": "a", "n": 1},
        user_id="u",
        request_id="r",
        cache_namespace="ns",
        cache_force_refresh=True,
        guardrail_policy="strict",
        properties={"env": "prod"},
    )
    headers = out["default_headers"]
    assert headers == gw.create_headers(
        config=GatewayConfig(cache=CacheConfig(ttl=300)),
        trace_id="t",
        session_id="s",
        session_name="flow",
        session_path="/a/b",
        metadata={"team": "a", "n": 1},
        user_id="u",
        request_id="r",
        cache_namespace="ns",
        cache_force_refresh=True,
        guardrail_policy="strict",
        properties={"env": "prod"},
    )
    assert json.loads(headers["x-agentcc-metadata"]) == {"team": "a", "n": 1}
    assert headers["X-Guardrail-Policy"] == "strict"
    assert headers["x-agentcc-cache-ttl"] == "300"
    # The key travels once, as api_key; it is never copied into a header here.
    assert not any(name.lower() == "authorization" for name in headers)


def test_every_argument_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        openai_kwargs("k", GW)  # type: ignore[misc]


def _fresh(code: str) -> str:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(ALL_PREFIXES) and k != "PYTHONPATH"
    }
    env["PYTHONPATH"] = str(Path(fi.__file__).resolve().parents[1])
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_calling_it_imports_no_openai() -> None:
    out = _fresh(
        "import sys; from fi.gateway import openai_kwargs; "
        "openai_kwargs(api_key='k', base_url='http://127.0.0.1:8090'); "
        "print(sorted(m for m in sys.modules if m == 'openai' or m.startswith('openai.')))"
    )
    assert out == "[]"


def test_a_stock_openai_client_sends_the_gateway_key_to_the_gateway(
    monkeypatch,
) -> None:
    """Only where the openai package is installed (the fixed CI line has none)."""
    openai = pytest.importorskip("openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "id": "c",
                "object": "chat.completion",
                "created": 1,
                "model": "m",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "hi"},
                    }
                ],
            },
        )

    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.example/v1")
    monkeypatch.setenv("OPENAI_ORG_ID", "org-1")
    client = openai.OpenAI(
        **openai_kwargs(api_key="gw-key", base_url=GW, session_id="s1"),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=0,
    )
    client.chat.completions.create(
        model="m", messages=[{"role": "user", "content": "x"}]
    )
    (request,) = seen
    assert str(request.url) == f"{GW}/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer gw-key"
    assert request.headers["x-agentcc-session-id"] == "s1"
    assert "sk-openai-secret" not in json.dumps(dict(request.headers))
    # As the docstring says: the OpenAI SDK reads OPENAI_ORG_ID itself.
    assert request.headers["openai-organization"] == "org-1"


def test_agentcc_deprecation_warning_is_a_future_warning() -> None:
    """PEP 565 hides DeprecationWarning outside __main__; a FutureWarning is shown."""
    assert issubclass(gw.AgentCCDeprecationWarning, FutureWarning)
    assert not issubclass(gw.AgentCCDeprecationWarning, DeprecationWarning)
    assert gw.AgentCCDeprecationWarning.__module__ == "fi.gateway._deprecation"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("default")
        warnings.warn("agentcc moved", gw.AgentCCDeprecationWarning, stacklevel=1)
    assert [w.category for w in caught] == [gw.AgentCCDeprecationWarning]


def test_a_suite_can_filter_it_by_class_without_importing_agentcc() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warnings.filterwarnings("ignore", category=gw.AgentCCDeprecationWarning)
        warnings.warn("agentcc moved", gw.AgentCCDeprecationWarning, stacklevel=1)
        with pytest.raises(FutureWarning):
            warnings.warn("another", FutureWarning, stacklevel=1)


def test_the_metadata_models_are_re_exported_at_the_top_level() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata, RateLimitInfo

    assert gw.AgentCCMetadata is AgentCCMetadata
    assert gw.RateLimitInfo is RateLimitInfo
    meta = gw.AgentCCMetadata.from_headers(
        httpx.Headers(
            {
                "x-agentcc-request-id": "req-1",
                "x-agentcc-cost": "0.25",
                "x-ratelimit-limit-requests": "100",
                "x-ratelimit-remaining-requests": "99",
            }
        )
    )
    assert meta.request_id == "req-1" and meta.cost == 0.25
    assert isinstance(meta.ratelimit, gw.RateLimitInfo)
