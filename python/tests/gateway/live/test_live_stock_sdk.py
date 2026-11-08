"""The stock OpenAI Python SDK pointed at agentcc-gateway the recorded source through openai_kwargs().

Proven here: the stock SDK on a cache hit and the stock SDK's OPENAI_* headers;
openai_kwargs() always passes an explicit key, so OPENAI_API_KEY never reaches the
gateway. Requests go through the wire tap, so the test sees exactly what the stock SDK
sent. Skipped when ``openai`` is not installed (run-wire-suite.sh installs a pinned one).
"""

from __future__ import annotations

import pytest

from ._live import Live, sha12, user

openai = pytest.importorskip("openai")
MODEL = "gpt-4o-mini"


@pytest.fixture
def stock(live: Live, monkeypatch: pytest.MonkeyPatch):
    from fi.gateway import openai_kwargs

    monkeypatch.setenv("OPENAI_API_KEY", "openai-key-that-must-not-be-sent")
    monkeypatch.setenv("OPENAI_ORG_ID", "org-live-stock")
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj-live-stock")
    kw = openai_kwargs(api_key=live.key, base_url=live.tap, session_id="s-stock", metadata={"tier": "gold"})
    c = openai.OpenAI(**kw, max_retries=0)
    yield c
    c.close()


def test_stock_sdk_identity_headers(live: Live, stock) -> None:
    m = live.marker()
    raw = stock.chat.completions.with_raw_response.create(model=MODEL, messages=user(f"stock {m}"))
    r = raw.parse()
    (rec,) = live.tap_records(m)
    (up,) = live.mock_records(m)
    h = rec["headers"]
    live.record("stock_py_headers", {
        "openai_version": openai.__version__, "sent_header_names": sorted(h),
        "authorization": h.get("authorization"), "openai-organization": h.get("openai-organization"),
        "openai-project": h.get("openai-project"), "x-agentcc": {k: v for k, v in h.items() if k.startswith("x-agentcc")},
        "upstream_forwarded": {k: up["headers"].get(k) for k in ("openai-organization", "openai-project")},
        "response_provider": raw.headers.get("x-agentcc-provider"), "content": r.choices[0].message.content})
    assert h["authorization"] == f"<sha256:{sha12(live.key)}>"  # never OPENAI_API_KEY
    assert h.get("x-agentcc-session-id") == "s-stock"
    assert raw.headers.get("x-agentcc-provider") == "mock-b"  # the metadata header was read
    # openai_kwargs' docstring: the stock SDK still sends OPENAI_ORG_ID / OPENAI_PROJECT_ID.
    assert h.get("openai-organization") == "org-live-stock"
    assert h.get("openai-project") == "proj-live-stock"


def test_stock_sdk_stream_and_cache_s3(live: Live, stock) -> None:
    m = live.marker()
    msgs = user(f"stock-cache {m}")
    warm = stock.chat.completions.with_raw_response.create(model=MODEL, messages=msgs)
    hit = stock.chat.completions.with_raw_response.create(model=MODEL, messages=msgs)
    chunks = list(stock.chat.completions.create(model=MODEL, messages=msgs, stream=True))
    text = "".join(c.choices[0].delta.content or "" for c in chunks if c.choices)
    live.record("stock_py_cache_s3", {"warm_cache": warm.headers.get("x-agentcc-cache"),
                                      "hit_cache": hit.headers.get("x-agentcc-cache"),
                                      "stream_chunks": len(chunks), "stream_text": text,
                                      "usage_chunks": [c.usage.model_dump() for c in chunks if c.usage]})
    assert (hit.headers.get("x-agentcc-cache") or "").startswith("hit")
    assert text == "Hello world"  # streams bypass the cache at the pin, so the stock SDK sees SSE


def test_stock_sdk_on_a_stream_block(live: Live, stock) -> None:
    """What the stock SDK does with the gateway's stream_blocked frame (fi.gateway raises StreamError)."""
    got, err = "", None
    try:
        for c in stock.chat.completions.create(model=MODEL, stream=True,
                                               messages=user(f"[[mock:block-mid]] {live.marker()}")):
            got += (c.choices[0].delta.content or "") if c.choices else ""
    except Exception as e:  # noqa: BLE001 - recording whatever the stock SDK raises
        err = e
    live.record("stock_py_stream_block", {"text": got, "error_class": err and type(err).__name__,
                                          "error": err and str(err)})
    assert err is not None and got == "Hello world"
