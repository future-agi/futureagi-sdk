"""D-21 reconciled with released compatibility adapters.

Historical test names remain stable for the census. Released names, positional
orders and config fields are retained with deprecation warnings, not removed.
The checked-in snapshot pins the union, including the unit-only additions.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import fi
import fi.gateway as gw
from fi.gateway import AgentCC, AsyncAgentCC, CacheConfig, GatewayConfig, TimeoutConfig

HERE = Path(__file__).resolve().parent
SNAPSHOT = json.loads((HERE.parent / "api_snapshot.json").read_text())
GOLDEN = (
    Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway" / "golden"
)
OLD_ALL = set(
    json.loads((GOLDEN / "py-agentcc-1.0.0" / "surface.json").read_text())["cases"][
        "surface.all[sync]"
    ]["result"]["__all__"]
)


def _fresh_dir() -> list[str]:
    """Check lazy exports independently of earlier imports in this process."""
    code = "import json, fi.gateway as g; print(json.dumps(sorted(n for n in dir(g) if not n.startswith('_'))))"
    env = {**os.environ, "PYTHONPATH": str(Path(fi.__file__).resolve().parents[1])}
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


KEPT_1_0 = 85
STARRED_TO_S = {"JSONLoggingCallbackHandler", "AgentCCLogger"}
DEPRECATED = {
    "AGENTCC_GATEWAY_URL", "AgentCCLogger", "AsyncGateway", "BudgetManager",
    "CONTENT_POLICY_FALLBACKS", "CONTEXT_WINDOW_FALLBACKS", "ConditionalRoutingConfig",
    "FallbackConfig", "FallbackTarget", "Gateway", "GuardrailCheck", "GuardrailConfig",
    "JSONLoggingCallbackHandler", "LoadBalanceConfig", "LoadBalanceTarget", "MODEL_INFO",
    "ModelInfo", "RetryConfig", "RoutingCondition", "TrafficMirrorConfig",
    "abatch_completion", "abatch_completion_models", "abatch_completion_models_all",
    "batch_completion", "batch_completion_models", "batch_completion_models_all",
    "completion_cost", "completion_cost_from_response", "decode", "encode",
    "get_content_policy_fallback", "get_context_window_fallback", "get_max_output_tokens",
    "get_max_tokens", "get_model_info", "get_valid_models", "is_prompt_caching_valid",
    "model_alias_map", "patch_openai", "register_model", "return_raw_request",
    "supports_function_calling", "supports_json_mode", "supports_response_schema",
    "supports_vision", "token_counter", "trim_messages", "validate_environment",
}


def test_the_root_surface_matches_the_snapshot() -> None:
    assert sorted(gw.__all__) == SNAPSHOT["fi.gateway"]["__all__"]
    assert len(gw.__all__) == KEPT_1_0 + len(SNAPSHOT["new_names"])
    assert _fresh_dir() == SNAPSHOT["fi.gateway"]["dir"]
    for name in gw.__all__:
        if name in DEPRECATED:
            with pytest.warns(DeprecationWarning, match=name):
                assert getattr(gw, name, None) is not None
        else:
            assert getattr(gw, name, None) is not None


@pytest.mark.parametrize(
    "module", sorted(m for m in SNAPSHOT if m.startswith("fi.gateway."))
)
def test_each_public_subpackage_matches_the_snapshot(module: str) -> None:
    mod = importlib.import_module(module)
    assert sorted(getattr(mod, "__all__", [])) == SNAPSHOT[module]["__all__"]


def test_the_kept_1_0_names_are_the_k_and_f_buckets() -> None:
    """Released S-bucket adapters are kept too, not just the original K/F names."""
    kept = OLD_ALL & set(gw.__all__)
    assert len(OLD_ALL) == 85
    assert len(kept) == KEPT_1_0, sorted(kept)
    assert STARRED_TO_S <= OLD_ALL and STARRED_TO_S <= set(gw.__all__)
    assert set(gw.__all__) - OLD_ALL == set(SNAPSHOT["new_names"])


@pytest.mark.parametrize(
    "name",
    [
        "AGENTCC_GATEWAY_URL", "BudgetManager", "FallbackConfig", "RetryConfig",
        "GuardrailConfig", "token_counter", "completion_cost", "get_model_info",
        "batch_completion", "patch_openai", "return_raw_request", "validate_environment",
    ],
)
def test_s_bucket_names_are_gone(name: str, monkeypatch) -> None:
    """Released adapters now resolve, warn on every lookup and retain identity."""
    assert name in OLD_ALL
    with pytest.warns(DeprecationWarning, match=name):
        value = getattr(gw, name, None)
    assert value is not None
    namespace = {}
    with pytest.warns(DeprecationWarning, match=name):
        exec(f"from fi.gateway import {name}", namespace)
    assert namespace[name] is value
    assert name in gw.__all__
    _assert_released_effect(name, value, monkeypatch)


def _assert_released_effect(name, value, monkeypatch):
    """Small deterministic effects; optional tokenizer and batch callers are fakes."""
    from types import SimpleNamespace

    for key in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(key, raising=False)
    if name == "AGENTCC_GATEWAY_URL":
        assert value == "https://gateway.futureagi.com/v1"
        return
    with pytest.warns(DeprecationWarning):
        if name == "BudgetManager":
            budget = value(max_budget=1)
            budget.update_cost(0.25)
            assert budget.get_current_spend() == 0.25
            assert budget.get_remaining_budget() == 0.75
            with pytest.raises(gw.AgentCCError, match="Budget exceeded"):
                budget.check_budget(1)
        elif name == "FallbackConfig":
            config = value()
            assert config.targets == [] and config.on_status_codes == [429, 500, 502, 503, 504]
        elif name == "RetryConfig":
            config = value(max_retries=3)
            assert config.max_retries == 3 and config.on_status_codes == [429, 500, 502, 503]
        elif name == "GuardrailConfig":
            config = value(input_guardrails=["policy"])
            assert config.input_guardrails == ["policy"] and config.deny is True
        elif name == "token_counter":
            encoding = SimpleNamespace(encode=lambda text: list(text))
            monkeypatch.setitem(sys.modules, "tiktoken", SimpleNamespace(encoding_for_model=lambda model: encoding))
            assert value("unit-model", text="abcd") == 4
            assert value("unit-model") == 0
        elif name in {"completion_cost", "get_model_info"}:
            from fi.gateway._models_info import MODEL_INFO

            info = MODEL_INFO["gpt-4o"]
            if name == "get_model_info":
                assert value("gpt-4o") is info
                assert value("unknown-unit-model") is None
            else:
                assert value("gpt-4o", prompt_tokens=2, completion_tokens=3) == (
                    2 * info.input_cost_per_token + 3 * info.output_cost_per_token
                )
                assert value("unknown-unit-model") is None
        elif name == "batch_completion":
            def create(*, model, messages, **kwargs):
                return (model, messages[0]["content"], kwargs)

            client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
            messages = [[{"role": "user", "content": text}] for text in ("a", "b")]
            assert value(client, "m", messages, max_concurrency=1, temperature=0) == [
                ("m", "a", {"temperature": 0}), ("m", "b", {"temperature": 0}),
            ]
        elif name == "patch_openai":
            with value(api_key="unit-key", base_url="https://gateway.example.test") as client:
                assert isinstance(client, AgentCC)
                assert client._base_url == "https://gateway.example.test"
        elif name == "return_raw_request":
            result = value(model="m", messages=[], api_key="unit-key", base_url="https://gateway.example.test")
            assert result["method"] == "POST"
            assert result["url"] == "https://gateway.example.test/v1/chat/completions"
            assert result["body"] == {"model": "m", "messages": []}
        elif name == "validate_environment":
            monkeypatch.setenv("AGENTCC_API_KEY", "unit-key")
            monkeypatch.setenv("AGENTCC_BASE_URL", "https://gateway.example.test")
            assert value() == {"keys_set": ["AGENTCC_API_KEY", "AGENTCC_BASE_URL"],
                               "keys_missing": [], "ready": True}
        else:
            pytest.fail(f"No released effect assertion for {name}")


@pytest.mark.filterwarnings('default:^AsyncModerations\\ is\\ a\\ deprecated\\ released\\ gateway\\ compatibility\\ API\\.:DeprecationWarning')
@pytest.mark.filterwarnings('default:^Moderations\\ is\\ a\\ deprecated\\ released\\ gateway\\ compatibility\\ API\\.:DeprecationWarning')
@pytest.mark.filterwarnings('default:^(Async)?Batches is a deprecated released gateway compatibility API\\.:DeprecationWarning')
@pytest.mark.filterwarnings('default:^AsyncBatches\\ is\\ a\\ deprecated\\ released\\ gateway\\ compatibility\\ API\\.:DeprecationWarning')
@pytest.mark.filterwarnings('default:^Batches\\ is\\ a\\ deprecated\\ released\\ gateway\\ compatibility\\ API\\.:DeprecationWarning')
@pytest.mark.filterwarnings('default:^client\\.batches is a deprecated released compatibility resource\\.:DeprecationWarning')
@pytest.mark.parametrize("cls", [AgentCC, AsyncAgentCC])
def test_batches_moderations_and_inert_options_are_gone(cls: type) -> None:
    """Released resources and options are deprecated adapters, not missing APIs."""
    client = cls(api_key="k", base_url="http://127.0.0.1:8090")
    for name in ("batches", "moderations"):
        with pytest.warns(DeprecationWarning, match=name):
            resource = getattr(client, name, None)
        assert resource is not None
        assert callable(getattr(resource, "create", None))
        assert resource._client is client
    params = inspect.signature(cls.__init__).parameters
    for option, value in (("redact_messages", True), ("pre_call_rules", []), ("modify_params", True)):
        assert option in params
        with pytest.warns(DeprecationWarning, match=option):
            configured = cls(api_key="k", base_url="http://127.0.0.1:8090", **{option: value})
        assert getattr(configured, f"_{option}") == value


@pytest.mark.parametrize(
    "section", ["fallback", "load_balance", "guardrails", "routing", "mirror", "retry"]
)
def test_an_unapplied_section_is_a_type_error_that_says_why(section: str) -> None:
    """Keep each released section and truthfully warn about backend support."""
    classes = {
        "fallback": "FallbackConfig", "load_balance": "LoadBalanceConfig",
        "guardrails": "GuardrailConfig", "routing": "ConditionalRoutingConfig",
        "mirror": "TrafficMirrorConfig", "retry": "RetryConfig",
    }
    with pytest.warns(DeprecationWarning, match=classes[section]):
        cls = getattr(gw, classes[section], None)
        assert callable(cls)
        value = cls()
    with pytest.warns(DeprecationWarning, match=section):
        config = GatewayConfig(**{section: value})
    assert getattr(config, section) is value
    with pytest.warns(DeprecationWarning, match="backend support is not guaranteed"):
        headers = config.to_headers()
    assert json.loads(headers["x-agentcc-config"]) == config.to_dict()
    assert section in config.to_dict()


@pytest.mark.parametrize(
    "cls, field",
    [
        (CacheConfig, "enabled"), (CacheConfig, "strategy"),
        (CacheConfig, "semantic_threshold"), (CacheConfig, "cache_by_model"),
        (CacheConfig, "ignore_keys"), (TimeoutConfig, "connect"),
        (TimeoutConfig, "read"), (TimeoutConfig, "write"), (TimeoutConfig, "pool"),
    ],
)
def test_unapplied_fields_are_type_errors(cls: type, field: str) -> None:
    values = {"enabled": False, "strategy": "semantic", "semantic_threshold": 0.8,
              "cache_by_model": False, "ignore_keys": ["user"]}
    value = values.get(field, 1)
    with pytest.warns(DeprecationWarning, match=field):
        section = cls(**{field: value})
    assert getattr(section, field) == value
    name = "cache" if cls is CacheConfig else "timeout"
    config = GatewayConfig(**{name: section})
    assert config.to_dict()[name][field] == value
    with pytest.warns(DeprecationWarning, match=f"{name}.{field}"):
        headers = config.to_headers()
    assert json.loads(headers["x-agentcc-config"])[name][field] == value


def test_a_misspelt_field_is_an_ordinary_type_error() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument 'ttl_seconds'"):
        CacheConfig(ttl_seconds=5)


def test_arguments_are_keyword_only() -> None:
    """Released positional order is accepted with a migration warning."""
    with pytest.warns(DeprecationWarning, match="FallbackConfig"):
        fallback = gw.FallbackConfig()
    with pytest.warns(DeprecationWarning, match="positional arguments"):
        config = GatewayConfig(fallback)
    assert config.fallback is fallback and config.cache is None
    with pytest.warns(DeprecationWarning, match="positional arguments"):
        cache = CacheConfig(False)
    assert cache.enabled is False and cache.ttl is None
    with pytest.warns(DeprecationWarning, match="positional arguments"):
        timeout = TimeoutConfig(30)
    assert timeout.connect == 30 and timeout.total is None


def test_to_headers_sends_only_the_cache_section_in_the_json() -> None:
    """Serialize the released full config while retaining the unit wire headers."""
    config = GatewayConfig(
        cache=CacheConfig(ttl=300, namespace="prod", force_refresh=True),
        timeout=TimeoutConfig(total=1.5),
    )
    expected = {
        "cache": {"enabled": True, "strategy": "exact", "ttl": 300,
                  "namespace": "prod", "force_refresh": True, "cache_by_model": True},
        "timeout": {"total": 1.5},
    }
    headers = config.to_headers()
    assert json.loads(headers["x-agentcc-config"]) == expected
    assert headers["x-agentcc-cache-ttl"] == "300"
    assert headers["x-agentcc-cache-namespace"] == "prod"
    assert headers["x-agentcc-cache-force-refresh"] == "true"
    assert headers["x-agentcc-request-timeout"] == "1500"
    assert "x-agentcc-guardrail-policy" not in headers
    assert config.to_dict() == expected


def test_a_timeout_only_config_sends_no_config_json() -> None:
    """The released JSON includes timeout as well as the dedicated wire header."""
    assert GatewayConfig(timeout=TimeoutConfig(total=2)).to_headers() == {
        "x-agentcc-config": '{"timeout":{"total":2}}',
        "x-agentcc-request-timeout": "2000",
    }
    assert GatewayConfig().to_headers() == {}


def test_configs_are_still_dataclasses_with_equality_and_repr() -> None:
    a = GatewayConfig(cache=CacheConfig(ttl=1))
    assert a == GatewayConfig(cache=CacheConfig(ttl=1)) and a != GatewayConfig()
    assert repr(a) == (
        "GatewayConfig(fallback=None, load_balance=None, "
        "cache=CacheConfig(enabled=True, strategy='exact', ttl=1, namespace=None, "
        "force_refresh=False, semantic_threshold=None, cache_by_model=True, ignore_keys=None), "
        "guardrails=None, routing=None, mirror=None, retry=None, timeout=None)"
    )
