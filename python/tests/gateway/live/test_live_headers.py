"""Request headers fi.gateway sends, and whether agentcc-gateway the recorded source reads them.

Proven here: D-06 (metadata as one JSON header), the x-agentcc-user-id effect, the
drop_params body effect, the FI_* / OPENAI_* isolation on the wire and
the no-stream_options invariant. The effect proofs use the conditional route in
stack/gateway.yaml: ``metadata.tier == "gold"`` sends the call to provider mock-b,
which the response's x-agentcc-provider names.
"""

from __future__ import annotations

import json

import pytest

from ._live import Live, sha12, user

MODEL = "gpt-4o-mini"
FORBIDDEN = ("x-api-key", "x-secret-key", "x-organization-id", "openai-organization", "openai-project")
FORBIDDEN_PREFIXES = ("x-workspace-", "x-omega-")


def _provider(live: Live, client, **kw) -> str:
    r = client.chat.completions.create(model=MODEL, messages=user(f"route {live.marker()}"), **kw)
    return r.agentcc.provider


def test_client_metadata_json_header_has_an_effect_d06(live: Live) -> None:
    from fi.gateway import AgentCC

    with AgentCC(api_key=live.key, base_url=live.base, metadata={"tier": "gold"}, max_retries=0) as c:
        gold = _provider(live, c)
    with AgentCC(api_key=live.key, base_url=live.base, metadata={"tier": "silver"}, max_retries=0) as c:
        silver = _provider(live, c)
    live.record("d06_client_metadata", {"tier=gold": gold, "tier=silver": silver})
    assert (gold, silver) == ("mock-b", "mock-a")


def test_session_metadata_json_header_has_an_effect_d06(live: Live, tapped) -> None:
    m = live.marker()
    with tapped.session(name="checkout", path="/cart", metadata={"tier": "gold"}):
        r = tapped.chat.completions.create(model=MODEL, messages=user(f"sess {m}"))
    (rec,) = live.tap_records(m)
    sent = {k: v for k, v in rec["headers"].items() if k.startswith("x-agentcc-")}
    live.record("d06_session_metadata", {"sent": sent, "provider": r.agentcc.provider})
    assert json.loads(sent["x-agentcc-metadata"])["tier"] == "gold"
    assert not [k for k in sent if k.startswith("x-agentcc-metadata-")]  # no per-key headers (D-06)
    assert r.agentcc.provider == "mock-b"


def test_per_key_metadata_headers_have_no_reader_d06(live: Live, client) -> None:
    """agentcc 1.x's x-agentcc-metadata-<k>: the gateway ignores it (no route change)."""
    per_key = _provider(live, client, extra_headers={"x-agentcc-metadata-tier": "gold"})
    json_hdr = _provider(live, client, extra_headers={"x-agentcc-metadata": json.dumps({"tier": "gold"})})
    live.record("d06_per_key_header", {"x-agentcc-metadata-tier": per_key, "x-agentcc-metadata": json_hdr})
    assert (per_key, json_hdr) == ("mock-a", "mock-b")


def test_properties_fold_into_metadata(live: Live, client) -> None:
    """x-agentcc-property-<k> is folded into metadata by the gateway (agentcc_config_header.go)."""
    assert _provider(live, client, properties={"tier": "gold"}) == "mock-b"
    assert _provider(live, client, properties={"tier": "bronze"}) == "mock-a"


def test_user_id_header_is_read_by_the_gateway(live: Live, tapped) -> None:
    """x-agentcc-user-id is an agent context field at the pin (models/agentctx_validate.go):
    validated on every request, used by per-user budgets and org rate limits. A value the
    gateway refuses proves the reader, although the header's literal name appears only in
    middleware/cors.go."""
    from fi.gateway import BadRequestError

    m = live.marker()
    ok = tapped.chat.completions.create(model=MODEL, messages=user(f"uid {m}"), user_id="user 42")
    (rec,) = live.tap_records(m)
    with pytest.raises(BadRequestError) as ei:
        tapped.chat.completions.create(model=MODEL, messages=user(f"uid-long {live.marker()}"), user_id="u" * 300)
    live.record("user_id_reader", {"sent": rec["headers"].get("x-agentcc-user-id"),
                                   "valid_status": 200, "invalid_status": ei.value.status_code,
                                   "invalid_body": ei.value.body})
    assert ok.choices[0].message.content == "PONG from mock"
    assert rec["headers"].get("x-agentcc-user-id") == "user 42"
    assert ei.value.status_code == 400
    assert "user" in json.dumps(ei.value.body).lower()


def test_drop_params_has_no_gateway_effect(live: Live, client) -> None:
    """The gateway has no drop_params reader at the pin: the upstream body is the same
    with and without it, apart from the field itself, which reaches the provider
    unchanged, and a parameter the provider may not support is not dropped. So
    drop_params is not a gateway option: a client that sends it passes a field the
    OpenAI API does not define through to the provider. The field goes as a raw body
    field, so the proof holds whatever client options exist."""
    bodies = {}
    for flag in (None, True):
        m = live.marker()
        extra = {"mock_unsupported_param": 7} if flag is None else {"mock_unsupported_param": 7, "drop_params": flag}
        client.chat.completions.create(model=MODEL, messages=user(f"dp {m}"), extra_body=extra)
        (rec,) = live.mock_records(m)
        body = dict(rec["body"])
        body["messages"] = "<marker>"
        bodies["with" if flag else "without"] = body
    live.record("drop_params_effect", bodies)
    without = bodies["without"]
    with_flag = {k: v for k, v in bodies["with"].items() if k != "drop_params"}
    assert with_flag == without
    assert bodies["with"].get("drop_params") is True
    assert "drop_params" not in without
    assert without.get("mock_unsupported_param") == 7


def test_no_fi_or_openai_identity_leaves_the_sdk(live: Live, monkeypatch: pytest.MonkeyPatch) -> None:
    """Section 2.1 wire test: every FI_* and OPENAI_* variable set; none reaches the wire."""
    from fi.gateway import AgentCC

    for name, value in {"FI_API_KEY": "fi-key-live", "FI_SECRET_KEY": "fi-secret-live",
                        "FI_PLATFORM_TOKEN": "fi-platform-live", "OPENAI_API_KEY": "openai-key-live",
                        "OPENAI_ORG_ID": "org-live", "OPENAI_PROJECT_ID": "proj-live",
                        "OPENAI_BASE_URL": "http://127.0.0.1:9/v1"}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("FI_GATEWAY_API_KEY", live.key)
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", live.tap)
    m = live.marker()
    with AgentCC(max_retries=0) as c:
        c.chat.completions.create(model=MODEL, messages=user(f"iso {m}"))
        list(c.chat.completions.create(model=MODEL, messages=user(f"iso-s {m}"), stream=True))
    recs = live.tap_records(m)
    names = sorted({k for r in recs for k in r["headers"]})
    live.record("env_isolation", {"header_names": names,
                                  "authorization": [r["headers"].get("authorization") for r in recs]})
    assert len(recs) == 2
    for r in recs:
        assert r["headers"]["authorization"] == f"<sha256:{sha12(live.key)}>"
        assert not [k for k in r["headers"] if k in FORBIDDEN or k.startswith(FORBIDDEN_PREFIXES)]
        assert "stream_options" not in (r["body"] or {})  # the wire invariant: never added


def test_fi_key_pair_as_gateway_key_is_refused(live: Live, monkeypatch: pytest.MonkeyPatch) -> None:
    from fi.gateway import AgentCC, AgentCCError

    monkeypatch.setenv("FI_API_KEY", live.key)
    seq = live.last_tap_seq()
    with pytest.raises(AgentCCError):
        AgentCC(api_key=live.key, base_url=live.tap)
    assert live.tap_since(seq) == []  # refused before anything was sent


def test_header_helpers_reach_the_gateway(live: Live) -> None:
    """create_headers' names as the gateway receives them."""
    from fi.gateway import AgentCC, create_headers

    hdrs = create_headers(trace_id="t-live", session_id="s-live", session_name="checkout", session_path="/a/b",
                          metadata={"tier": "gold"}, user_id="user 7", request_id="r-live", cache_ttl=60,
                          cache_namespace="ns-live", cache_force_refresh=True, properties={"env": "prod"})
    m = live.marker()
    with AgentCC(api_key=live.key, base_url=live.tap, default_headers=hdrs, max_retries=0) as c:
        r = c.chat.completions.create(model=MODEL, messages=user(f"helpers {m}"))
    (rec,) = live.tap_records(m)
    sent = {k: v for k, v in rec["headers"].items() if k.startswith("x-agentcc-")}
    live.record("header_helpers", {"built": hdrs, "received": sent, "agentcc": r.agentcc.model_dump()})
    assert {k.lower(): v for k, v in hdrs.items()}.items() <= sent.items()
    assert r.agentcc.provider == "mock-b"  # the JSON metadata header was read
    assert r.agentcc.client_request_id == "r-live"
