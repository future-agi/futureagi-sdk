"""fi.gateway against agentcc-gateway the recorded source: routes, metadata, base URLs, health.

Proven here against the running gateway: D-07, D-09, D-10, batches and moderations
404, /health 404, D-15 (current_cost, with_options trace id) and the response
metadata fi.gateway reads, including fallback_used (org-fallback, whose org config turns
failover and a model fallback chain on) and routing_strategy (mock-routed, the model
with two routing targets). Each test writes what it saw to the evidence directory.
"""

from __future__ import annotations

import json

import httpx
import pytest

from ._live import Live, sha12, user

MODEL = "gpt-4o-mini"


def test_chat_create_reads_gateway_metadata_d10(live: Live, client) -> None:
    m = live.marker()
    r = client.chat.completions.create(model=MODEL, messages=user(f"ping {m}"), request_id="cli-req-d10")
    meta = r.agentcc
    live.record("d10_metadata", {"content": r.choices[0].message.content, "agentcc": meta.model_dump()})
    assert r.choices[0].message.content == "PONG from mock"
    assert meta.request_id not in ("", "unknown")
    assert meta.provider == "mock-a"
    assert meta.client_request_id == "cli-req-d10"  # D-10: X-Agentcc-Client-Request-Id
    assert meta.request_id != "cli-req-d10"  # the gateway's own id stays separate
    assert meta.cost is not None and meta.cost > 0  # custom_pricing in stack/gateway.yaml
    assert meta.latency_ms >= 0


def test_request_timeout_and_model_used_metadata(live: Live, tapped) -> None:
    """request_timeout= sends x-agentcc-request-timeout (ms), which the
    gateway applies and echoes as x-agentcc-timeout-ms; model_used is the upstream's model."""
    m = live.marker()
    r = tapped.chat.completions.create(model=MODEL, messages=user(f"timeout {m}"), request_timeout=5000)
    (sent,) = live.tap_records(m)
    live.record("request_timeout_model_used", {"agentcc": r.agentcc.model_dump(),
                                               "sent_timeout": sent["headers"].get("x-agentcc-request-timeout")})
    assert sent["headers"].get("x-agentcc-request-timeout") == "5000"
    assert r.agentcc.timeout_ms == 5000
    assert r.agentcc.model_used == MODEL


def _raw_chat(live: Live, key: str, model: str, text: str) -> tuple[int, dict]:
    with live.raw() as c:
        resp = c.post("/v1/chat/completions", json={"model": model, "messages": user(text)},
                      headers=live.auth(key))
    return resp.status_code, {k: v for k, v in resp.headers.items() if k.startswith("x-agentcc-")}


def test_model_fallback_sets_fallback_used_and_model_used(live: Live) -> None:
    """The mock answers 503 for mock-fails; org-fallback's failover
    moves the request down its chain to gpt-4o-mini, and the gateway says so in
    x-agentcc-fallback-used and x-agentcc-model-used, which fi.gateway reads."""
    from fi.gateway import AgentCC

    key = live.keys["fallback"]["key"]
    m = live.marker()
    status, raw = _raw_chat(live, key, "mock-fails", f"fb-raw {m}")
    with AgentCC(api_key=key, base_url=live.base, max_retries=0) as c:
        r = c.chat.completions.create(model="mock-fails", messages=user(f"fb {m}"))
    upstream = [rec["body"]["model"] for rec in live.mock_records(m) if "fb " in json.dumps(rec["body"])]
    live.record("fallback_used_model_used", {"raw_status": status, "raw_headers": raw,
                                             "agentcc": r.agentcc.model_dump(), "upstream_models": upstream})
    assert status == 200 and raw.get("x-agentcc-fallback-used") == "true"
    assert raw.get("x-agentcc-model-used") == "gpt-4o-mini"
    assert r.agentcc.fallback_used is True
    assert r.agentcc.model_used == "gpt-4o-mini"
    assert r.choices[0].message.content == "PONG from mock"
    assert upstream[0] == "mock-fails" and upstream[-1] == "gpt-4o-mini"


def test_routing_strategy_is_read_for_a_routed_model(live: Live, client) -> None:
    """mock-routed has two routing targets (stack/gateway.yaml), so
    the router picks one with its strategy and the gateway names it in
    x-agentcc-routing-strategy; a model with one provider gets none."""
    m = live.marker()
    status, raw = _raw_chat(live, live.key, "mock-routed", f"rs-raw {m}")
    r = client.chat.completions.create(model="mock-routed", messages=user(f"rs {m}"))
    single = client.chat.completions.create(model=MODEL, messages=user(f"rs-single {m}"))
    live.record("routing_strategy", {"raw_status": status, "raw_headers": raw, "agentcc": r.agentcc.model_dump(),
                                     "single_provider_routing_strategy": single.agentcc.routing_strategy})
    assert status == 200 and raw.get("x-agentcc-routing-strategy")
    assert r.agentcc.routing_strategy == raw["x-agentcc-routing-strategy"]
    assert r.agentcc.provider in {"mock-a", "mock-b"}
    assert single.agentcc.routing_strategy is None


def test_config_ignored_is_read_d10(live: Live, client) -> None:
    m = live.marker()
    cfg = {"cache": {"ttl": 60, "strategy": "semantic"}, "fallback": {"targets": [{"model": "x"}]}}
    r = client.chat.completions.create(model=MODEL, messages=user(f"cfg {m}"),
                                       extra_headers={"x-agentcc-config": json.dumps(cfg)})
    live.record("d10_config_ignored", {"sent": cfg, "config_ignored": r.agentcc.config_ignored})
    assert r.agentcc.config_ignored == ["cache.strategy", "fallback"]


def test_absent_config_ignored_is_none_d10(live: Live, client) -> None:
    r = client.chat.completions.create(model=MODEL, messages=user(f"plain {live.marker()}"))
    assert r.agentcc.config_ignored is None
    assert r.agentcc.client_request_id is None


@pytest.mark.parametrize("suffix", ["", "/", "/v1", "/v1/"])
def test_base_url_forms_reach_the_same_routes_d07(live: Live, suffix: str) -> None:
    from fi.gateway import AgentCC

    with AgentCC(api_key=live.key, base_url=live.base + suffix, max_retries=0) as c:
        r = c.chat.completions.create(model=MODEL, messages=user(f"d07 {live.marker()}"))
        models = c.models.list()
    assert r.choices[0].message.content == "PONG from mock"
    assert MODEL in [x.id for x in models.data]


def test_doubled_v1_is_a_gateway_404_d07(live: Live) -> None:
    """Why D-07 strips one /v1: FA's management API hands out base_url + "/v1"."""
    with live.raw() as c:
        doubled = c.get("/v1/v1/models", headers=live.auth())
        single = c.get("/v1/models", headers=live.auth())
    live.record("d07_doubled_v1", {"/v1/v1/models": doubled.status_code, "/v1/models": single.status_code,
                                   "doubled_body": doubled.text[:300]})
    assert doubled.status_code == 404
    assert single.status_code == 200


def test_health_check_uses_healthz_and_health_is_404_d09(live: Live) -> None:
    from fi.gateway import health_check

    result = health_check(api_key=live.key, base_url=live.base)
    with live.raw() as c:
        statuses = {p: c.get(p).status_code for p in ("/health", "/healthz", "/livez", "/readyz")}
    live.record("d09_health", {"health_check": result, "statuses": statuses})
    assert statuses["/health"] == 404  # agentcc 1.x asked here
    assert statuses["/healthz"] == 200
    assert result["status"] == "ok", result
    with_model = health_check(model=MODEL, api_key=live.key, base_url=live.base)
    assert with_model["status"] == "ok", with_model


@pytest.mark.parametrize("path", ["/v1/batches", "/v1/moderations"])
def test_batches_and_moderations_are_not_served(live: Live, client, path: str) -> None:
    body = {"input": "hello", "model": MODEL} if "moderations" in path else {
        "input_file_id": "file-x", "endpoint": "/v1/chat/completions", "completion_window": "24h"}
    with live.raw() as c:
        resp = c.post(path, json=body, headers=live.auth())
        listing = c.get(path, headers=live.auth())
    live.record(f"route_{path.strip('/').replace('/', '_')}", {"POST": resp.status_code, "GET": listing.status_code,
                                                               "body": resp.text[:300]})
    assert resp.status_code == 404
    assert listing.status_code in (404, 405)
    name = path.rsplit("/", 1)[1]
    with pytest.warns(DeprecationWarning, match=name):
        resource = getattr(client, name, None)
    assert resource is not None
    assert callable(getattr(resource, "create", None))
    # The adapter still sends the released route; this server does not serve it.
    from fi.gateway import NotFoundError

    with pytest.raises(NotFoundError) as error:
        if name == "batches":
            resource.create(requests=[])
        else:
            resource.create(input="hello", model=MODEL)
    assert error.value.status_code == 404


def test_virtual_key_never_reaches_the_upstream(live: Live, client) -> None:
    m = live.marker()
    client.chat.completions.create(model=MODEL, messages=user(f"auth {m}"))
    (rec,) = live.mock_records(m)
    sent = rec["headers"].get("authorization", "")
    # Recorded as comparisons only: a hash prefix next to a key-like name trips the pull scanner.
    live.record("upstream_auth", {"upstream_gets_the_virtual_key": sha12(live.key) in sent,
                                  "upstream_gets_the_provider_key": bool(live.upstream_key_sha12)
                                  and sent == f"<sha256:{live.upstream_key_sha12}>"})
    assert sha12(live.key) not in sent
    if live.upstream_key_sha12:
        assert sent == f"<sha256:{live.upstream_key_sha12}>"


def test_current_cost_sums_the_gateway_cost_d15(live: Live) -> None:
    from fi.gateway import AgentCC

    with AgentCC(api_key=live.key, base_url=live.base, max_retries=0) as c:
        costs = [c.chat.completions.create(model=MODEL, messages=user(f"cost {i} {live.marker()}")).agentcc.cost
                 for i in range(3)]
        total = c.current_cost
    live.record("d15_current_cost", {"costs": costs, "current_cost": total})
    assert all(x and x > 0 for x in costs)
    assert total == pytest.approx(sum(costs))


def test_with_options_trace_id_reaches_the_gateway_d15(live: Live, tapped) -> None:
    m = live.marker()
    derived = tapped.with_options(trace_id="trace-d15-live")
    r = derived.chat.completions.create(model=MODEL, messages=user(f"trace {m}"))
    (rec,) = live.tap_records(m)
    live.record("d15_trace_id", {"sent_header": rec["headers"].get("x-agentcc-trace-id"),
                                 "echoed": r.agentcc.trace_id})
    assert rec["headers"].get("x-agentcc-trace-id") == "trace-d15-live"
    assert r.agentcc.trace_id == "trace-d15-live"


def test_check_valid_key(live: Live) -> None:
    from fi.gateway import check_valid_key

    assert check_valid_key(live.key, live.base) is True
    assert check_valid_key("not-a-minted-gateway-key", live.base) is False


def test_error_envelopes_and_classes(live: Live) -> None:
    """Gateway error answers at the pin: status, envelope and the class fi.gateway raises."""
    from fi.gateway import AgentCC, APIStatusError

    seen = {}
    cases = {
        "bad_key": ("not-a-minted-gateway-key", MODEL, "x"),
        "unknown_model": (live.key, "no-such-model", "x"),
        "upstream_500": (live.key, MODEL, "[[mock:status:500]]"),
        "upstream_429": (live.key, MODEL, "[[mock:status:429]]"),
        "upstream_400": (live.key, MODEL, "[[mock:status:400]]"),
    }
    for name, (key, model, prompt) in cases.items():
        with AgentCC(api_key=key, base_url=live.base, max_retries=0) as c:
            with pytest.raises(APIStatusError) as ei:
                c.chat.completions.create(model=model, messages=user(f"{prompt} {live.marker()}"))
        e = ei.value
        seen[name] = {"class": type(e).__name__, "status": e.status_code, "message": str(e),
                      "body": getattr(e, "body", None)}
    live.record("error_envelopes", seen)
    assert seen["bad_key"]["status"] == 401 and seen["bad_key"]["class"] == "AuthenticationError"
    for row in seen.values():
        body = row["body"]
        assert isinstance(body, dict) and isinstance(body.get("error"), dict), row
        assert body["error"].get("message"), row  # the envelope carries error.message


def test_models_list(live: Live, client) -> None:
    models = client.models.list()
    live.record("models_list", {"models": [x.id for x in models.data]})
    assert {"gpt-4o-mini", "mock-b-only"} <= {x.id for x in models.data}


def test_embeddings_raw_usage_shape(live: Live) -> None:
    """What the gateway answers for /v1/embeddings: OpenAI's shape, usage without completion_tokens."""
    with live.raw() as c:
        resp = c.post("/v1/embeddings", json={"model": "text-embedding-3-small", "input": ["a", "b"]},
                      headers=live.auth())
    live.record("embeddings_raw", {"status": resp.status_code, "body": resp.json()})
    assert resp.status_code == 200
    assert "completion_tokens" not in resp.json()["usage"]


def test_embeddings_create(live: Live, client) -> None:
    """The gateway's embeddings answer (usage without completion_tokens) parses."""
    emb = client.embeddings.create(model="text-embedding-3-small", input=["a", "b"])
    live.record("embeddings_create", {"data": len(emb.data), "usage": emb.usage.model_dump()})
    assert len(emb.data) == 2 and emb.data[0].embedding == [0.1, 0.2, 0.3]
    assert emb.usage.prompt_tokens == 2 and emb.usage.total_tokens == 2


def test_the_gateway_itself_adds_stream_options_include_usage_upstream(live: Live) -> None:
    """A raw stream request without stream_options reaches the upstream with
    stream_options.include_usage set: the gateway adds it. The SDK's side of the wire
    invariant (it never sends stream_options) is asserted on the wire tap by
    test_live_streams and test_live_headers."""
    m = live.marker()
    status, _, _ = live.sse("/v1/chat/completions", {"model": MODEL, "stream": True, "messages": user(f"so {m}")})
    (rec,) = live.mock_records(m)
    live.record("upstream_stream_options", {"status": status, "upstream_body_keys": sorted(rec["body"].keys()),
                                            "stream_options": rec["body"].get("stream_options")})
    assert status == 200
    assert rec["body"].get("stream_options") == {"include_usage": True}


def test_mock_health_of_stack(live: Live) -> None:
    assert httpx.get(f"{live.base}/healthz", timeout=5).status_code == 200


def test_admin_minted_byok_key_is_barred_from_config_providers(live: Live) -> None:
    """A key minted with POST /-/keys and the admin token is type byok at the pin: it
    authenticates, but may use only its org's own providers (handlers.go resolveProviderFor),
    so a config-file provider answers 403. fi.gateway surfaces the gateway's message. (An
    org provider on a private address, with AGENTCC_ALLOW_PRIVATE_PROVIDER_URLS=true and
    enabled: true, would serve such a key; this stack's mock is on loopback, which the
    gateway refuses as a provider URL.)"""
    from fi.gateway import AgentCC, APIStatusError, PermissionDeniedError

    byok = live.keys["byok"]
    with AgentCC(api_key=byok["key"], base_url=live.base, max_retries=0) as c:
        try:
            listed: object = [m.id for m in c.models.list().data]
        except APIStatusError as e:
            listed = {"status": e.status_code, "message": str(e)}
        with pytest.raises(PermissionDeniedError) as ei:
            c.chat.completions.create(model=MODEL, messages=user(f"byok {live.marker()}"))
    live.record("byok_minted_key", {"key_type": byok.get("key_type"), "via": byok.get("via"),
                                    "models_listed": listed,
                                    "chat_status": ei.value.status_code, "chat_message": str(ei.value)})
    assert ei.value.status_code == 403
    assert "not available for this API key" in str(ei.value)
