"""Streams, guardrail blocks and the cache against agentcc-gateway the recorded source.

A gateway error frame on a 200 SSE stream raises a typed StreamError (type, code,
param), and usage comes from the finish chunk without stream_options. Also D-05 (guardrail IDs sent as a policy), D-16 (a late
error raises before ``done``) and a stream request on a warm cache entry. The keyword
guardrail in stack/gateway.yaml blocks the mock's answers that carry the block word;
``[[mock:...]]`` tags pick where in the stream the word comes.
"""

from __future__ import annotations

import json

import pytest

from ._live import Live, data_frames, user

MODEL = "gpt-4o-mini"


def _drain(stream) -> tuple[list, str, object]:
    """(chunks, text, the StreamError or None) of a chat stream."""
    from fi.gateway import StreamError

    chunks, text = [], ""
    try:
        for ch in stream:
            chunks.append(ch)
            for c in ch.choices:
                text += c.delta.content or ""
    except StreamError as e:
        return chunks, text, e
    return chunks, text, None


@pytest.mark.parametrize("scenario,before,text", [
    ("block-mid", 2, "Hello world"),  # fixture guardrail_block_after_content_then_done
    ("block-first", 0, ""),  # fixture guardrail_block_first_frame
])
def test_stream_blocked_raises_typed_stream_error(live: Live, client, scenario: str, before: int, text: str) -> None:
    stream = client.chat.completions.create(model=MODEL, stream=True,
                                            messages=user(f"[[mock:{scenario}]] {live.marker()}"))
    chunks, got, err = _drain(stream)
    live.record(f"stream_{scenario}", {"chunks": len(chunks), "text": got, "error": err and {
        "class": type(err).__name__, "message": str(err), "type": err.type, "code": err.code,
        "param": err.param, "body": err.body}})
    assert err is not None, "the gateway's stream_blocked frame must raise"
    assert (err.type, err.code) == ("guardrail_error", "stream_blocked")
    assert err.param is None and isinstance(err.body, dict)
    assert len(chunks) == before and got == text


def test_stream_blocked_at_finish_raises_before_the_metadata_chunk(live: Live, client) -> None:
    stream = client.chat.completions.create(model=MODEL, stream=True,
                                            messages=user(f"[[mock:block-finish]] {live.marker()}"))
    chunks, got, err = _drain(stream)
    live.record("stream_block-finish", {"chunks": len(chunks), "text": got,
                                        "error": err and {"type": err.type, "code": err.code, "message": str(err)}})
    assert err is not None and err.code == "stream_blocked"
    assert all(ch.choices for ch in chunks)  # the gateway's choices-[] metadata chunk never reached the caller
    assert got == f"Hello {live.block_word}"  # sent before the Finish check ran (under check_interval)


def test_stream_cut_by_the_deadline(live: Live, client) -> None:
    """The model deadline cuts the stream after "Partial". When the gateway sends its gateway_timeout
    frame, fi.gateway raises StreamError; at the recorded source it usually sends none (test_live_frames
    KNOWN_GATEWAY_DIFFERENCES), and the partial text then ends like a complete answer: recorded as xfail."""
    stream = client.chat.completions.create(model="mock-slow", stream=True,
                                            messages=user(f"[[mock:stall]] {live.marker()}"))
    chunks, got, err = _drain(stream)
    finish = [c.choices[0].finish_reason for c in chunks if c.choices]
    live.record("stream_deadline_cut", {"chunks": len(chunks), "text": got, "finish_reasons": finish,
                                        "error": err and {"type": err.type, "code": err.code, "message": str(err)}})
    assert got == "Partial"
    if err is None:
        pytest.xfail("gateway live-gateway-source sent no gateway_timeout frame for the deadline cut; the stream ended "
                     "after the partial answer with no finish_reason and no [DONE]")
    assert err.code == "gateway_timeout"


def test_stream_manager_late_error_raises_before_done_d16(live: Live, client) -> None:
    from fi.gateway import StreamError

    events = []
    with pytest.raises(StreamError) as ei:
        with client.chat.completions.stream(model=MODEL,
                                            messages=user(f"[[mock:block-finish]] {live.marker()}")) as s:
            for ev in s:
                events.append(ev.type)
    live.record("d16_late_error", {"events": events, "code": ei.value.code})
    assert "done" not in events
    assert ei.value.code == "stream_blocked"


def test_stream_usage_from_the_finish_chunk_without_stream_options(live: Live, tapped) -> None:
    m = live.marker()
    with tapped.chat.completions.stream(model=MODEL, messages=user(f"usage {m}")) as s:
        events = [ev.type for ev in s]
        final = s.get_final_completion()
    (rec,) = live.tap_records(m)
    (up,) = live.mock_records(m)
    live.record("stream_usage", {"events": events, "usage": final.usage.model_dump() if final.usage else None,
                                 "text": final.choices[0].message.content,
                                 "sdk_body_keys": sorted(rec["body"]), "upstream_body_keys": sorted(up["body"])})
    assert "stream_options" not in rec["body"]
    assert final.choices[0].message.content == "Hello world"
    assert final.usage is not None and final.usage.total_tokens > 0
    # The gateway sends the usage twice (the finish chunk, then its trailing choices-[]
    # chunk); the SDK emits one usage event per stream.
    assert events[-1] == "done" and events.count("usage") == 1


def test_nonstream_guardrail_block_status_and_class(live: Live, client) -> None:
    """The gateway refuses a blocked answer with 403 type guardrail_error (models.ErrGuardrailBlocked);
    fi.gateway's GuardrailBlockedError is keyed to 446, which this gateway never sends."""
    from fi.gateway import APIStatusError

    with pytest.raises(APIStatusError) as ei:
        client.chat.completions.create(model=MODEL, messages=user(f"[[mock:block-mid]] {live.marker()}"))
    e = ei.value
    resp = getattr(e, "response", None)
    live.record("nonstream_block", {"class": type(e).__name__, "status": e.status_code, "body": e.body,
                                    "message": str(e), "guardrail_headers": {
                                        k: v for k, v in (resp.headers.items() if resp is not None else [])
                                        if "guardrail" in k.lower()}})
    assert e.status_code == 403
    assert e.body["error"]["type"] == "guardrail_error"


def test_guardrail_log_only_answer_carries_the_outcome_headers(live: Live) -> None:
    """The guardrail readers: a log-only policy serves the answer the rule
    matched, with the gateway's outcome headers (response_evidence.go setGuardrailOutcomeHeaders:
    x-agentcc-guardrail-triggered, -action and x-agentcc-guardrails-triggered, the names)."""
    from fi.gateway import AgentCC

    with AgentCC(api_key=live.override_key, base_url=live.base, max_retries=0) as c:
        r = c.chat.completions.create(model=MODEL, messages=user(f"[[mock:block-mid]] {live.marker()}"),
                                      guardrail_policy="log-only")
    headers = {k: v for k, v in r.agentcc.http_response.headers.items() if "guardrail" in k.lower()}
    live.record("guardrail_log_only_headers", {"headers": headers, "agentcc": r.agentcc.model_dump(),
                                               "content": r.choices[0].message.content})
    assert live.block_word in r.choices[0].message.content  # served, not blocked
    assert r.agentcc.guardrail_triggered is True
    assert headers.get("x-agentcc-guardrail-action") == "log"
    assert headers.get("x-agentcc-guardrails-triggered") == "keyword-blocklist"


def test_guardrail_ids_sent_as_policy_are_refused_d05(live: Live) -> None:
    """agentcc 1.x's full GatewayConfig sent guardrail IDs as x-agentcc-guardrail-policy, which the
    gateway now reads as X-Guardrail-Policy (a mode): 403 without allow_policy_override, 400 with it."""
    body = {"model": MODEL, "messages": user(f"d05 {live.marker()}")}
    hdr = {"x-agentcc-guardrail-policy": "pii-detection,toxicity"}
    with live.raw() as c:
        plain = c.post("/v1/chat/completions", json=body, headers={**live.auth(), **hdr})
        override = c.post("/v1/chat/completions", json=body, headers={**live.auth(live.override_key), **hdr})
    live.record("d05_guardrail_ids_as_policy", {
        "plain_key": {"status": plain.status_code, "body": plain.json()},
        "override_key": {"status": override.status_code, "body": override.json()}})
    assert plain.status_code == 403
    assert override.status_code == 400 and override.json()["error"]["code"] == "invalid_policy"


def test_guardrail_policy_param_has_an_effect(live: Live) -> None:
    """guardrail_policy= sends X-Guardrail-Policy: "disabled" lets the blocked stream through
    for a key with allow_policy_override, and is refused for a key without it."""
    from fi.gateway import AgentCC, PermissionDeniedError

    prompt = user(f"[[mock:block-mid]] {live.marker()}")
    with AgentCC(api_key=live.override_key, base_url=live.base, max_retries=0) as c:
        _, text, err = _drain(c.chat.completions.create(model=MODEL, messages=prompt, stream=True,
                                                        guardrail_policy="disabled"))
    with AgentCC(api_key=live.key, base_url=live.base, max_retries=0) as c:
        with pytest.raises(PermissionDeniedError) as ei:
            list(c.chat.completions.create(model=MODEL, messages=prompt, stream=True, guardrail_policy="disabled"))
    live.record("guardrail_policy_effect", {"override_text_len": len(text), "override_error": err and err.code,
                                            "plain_status": ei.value.status_code})
    assert err is None and live.block_word in text
    assert ei.value.status_code == 403


def test_nonstream_cache_hit_and_streams_bypass_the_cache_s3(live: Live, client) -> None:
    """At the pin the cache plugin skips stream requests (plugins/cache/plugin.go), so a warm
    entry never answers stream:true with JSON; the stream is served from the upstream as SSE."""
    m = live.marker()
    msgs = user(f"cache {m}")
    first = client.chat.completions.create(model=MODEL, messages=msgs, cache_ttl=120)
    second = client.chat.completions.create(model=MODEL, messages=msgs, cache_ttl=120)
    status, headers, lines = live.sse("/v1/chat/completions", {"model": MODEL, "messages": msgs, "stream": True},
                                      {"x-agentcc-cache-ttl": "120"})
    chunks, text, err = _drain(client.chat.completions.create(model=MODEL, messages=msgs, stream=True, cache_ttl=120))
    upstream = live.mock_records(m)
    live.record("s3_cache_and_streams", {
        "first_cache": first.agentcc.cache_status, "second_cache": second.agentcc.cache_status,
        "stream_status": status, "stream_content_type": headers.get("content-type"),
        "stream_cache_header": headers.get("x-agentcc-cache"), "stream_frames": data_frames(lines),
        "sdk_stream_text": text, "upstream_calls": len(upstream)})
    assert (second.agentcc.cache_status or "").startswith("hit")  # x-agentcc-cache: hit_exact
    assert headers.get("content-type", "").startswith("text/event-stream")
    assert err is None and text == "Hello world"
    assert len(upstream) == 3  # one fill, then two streams; the hit never reached the upstream


def test_raw_stream_error_frame_shape(live: Live) -> None:
    status, headers, lines = live.sse("/v1/chat/completions", {
        "model": MODEL, "stream": True, "messages": user(f"[[mock:block-mid]] {live.marker()}")})
    frames = data_frames(lines)
    errors = [json.loads(f) for f in frames if f.startswith('{"error"')]
    live.record("raw_stream_block_frames", {"status": status, "frames": frames})
    assert status == 200 and len(errors) == 1
    assert sorted(errors[0]["error"]) == ["code", "message", "param", "type"]
