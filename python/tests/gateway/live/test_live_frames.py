"""Re-record tests/fixtures/gateway/stream-error-frames.json at agentcc-gateway the recorded source.

The fixture's six cases were written from gateway source the recorded source. Here each case is
produced by the real gateway (the mock upstream's scenario picks where the keyword
guardrail fires, or stalls past the model deadline), captured as raw SSE data frames,
and compared with the fixture case by case. The re-recording is written to the
evidence directory in the fixture's own format, with the per-case differences.

What the SDKs rely on: every error frame is
``{"error": {"message", "type", "param", "code"}}`` with the fixture's type and code.
Other differences (an extra metadata chunk, a [DONE] or not) are recorded, not failed:
the evidence lists each one for review.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from ._live import Live, data_frames, user

FIXTURE = pathlib.Path(__file__).resolve().parents[3].parent / "tests" / "fixtures" / "gateway" / "stream-error-frames.json"
CASES = {
    "guardrail_block_after_content_then_done": ("gpt-4o-mini", "block-mid"),
    "guardrail_block_at_finish_then_metadata_then_done": ("gpt-4o-mini", "block-finish"),
    "guardrail_block_first_frame": ("gpt-4o-mini", "block-first"),
    "upstream_timeout_cut_after_content": ("mock-slow", "stall"),
    "normal_stream": ("gpt-4o-mini", "no-usage"),
    "usage_chunk_with_empty_choices": ("gpt-4o-mini", "usage-chunk"),
}
# Error-frame differences at the recorded source that the gateway, not the fixture, owns. Each
# entry is what the pin actually sends; the test fails if that changes, so a gateway
# fix shows up here (and the SDK tests marked xfail for it start passing).
KNOWN_GATEWAY_DIFFERENCES = {
    "upstream_timeout_cut_after_content": {
        "kinds": [["chunk(role,content)"],
                  ["chunk(role,content)", "error(gateway_timeout/gateway_timeout;keys=code,message,param,type)"]],
        "why": "the model deadline (routing.model_timeouts) usually cuts the stream with no error frame and "
               "no [DONE]: the request context carries the timeout (handlers.go, context.WithTimeout before "
               "handleStream) and handleStream's select can take ctx.Done() (finalizeStream(true), return) "
               "before the closed-channel branch that writes streamCutError. A client then cannot tell the "
               "cut from a complete stream. Either outcome is accepted and recorded.",
    },
}
_recorded: dict[str, list[str]] = {}


def kind(frame: str) -> str:
    """A frame's shape, without ids, times or text."""
    if frame == "[DONE]":
        return "[DONE]"
    obj = json.loads(frame)
    if "error" in obj:
        e = obj["error"]
        return f"error({e.get('type')}/{e.get('code')};keys={','.join(sorted(e))})"
    choices = obj.get("choices") or []
    if not choices:
        return "chunk(choices=[]" + (",usage" if obj.get("usage") else "") + ")"
    c = choices[0]
    parts = [k for k in ("role", "content") if k in (c.get("delta") or {})]
    if c.get("finish_reason"):
        parts.append(f"finish={c['finish_reason']}")
    if obj.get("usage"):
        parts.append("usage")
    return "chunk(" + ",".join(parts or ["empty"]) + ")"


@pytest.fixture(scope="module")
def fixture_cases() -> dict[str, dict]:
    return {c["name"]: c for c in json.loads(FIXTURE.read_text())["cases"]}


@pytest.mark.parametrize("name", list(CASES))
def test_rerecord_case(live: Live, fixture_cases: dict, name: str) -> None:
    model, scenario = CASES[name]
    status, headers, lines = live.sse("/v1/chat/completions", {
        "model": model, "stream": True, "messages": user(f"[[mock:{scenario}]] {live.marker()}")})
    frames = data_frames(lines)
    _recorded[name] = frames
    old = [kind(f) for f in fixture_cases[name]["frames"]]
    new = [kind(f) for f in frames]
    live.record(f"frames_{name}", {"status": status, "content_type": headers.get("content-type"),
                                   "frames": frames, "kinds_live-gateway-source": new, "kinds_stream-fixture-source": old,
                                   "same_kinds": old == new})
    assert status == 200
    if name in KNOWN_GATEWAY_DIFFERENCES:
        assert new in KNOWN_GATEWAY_DIFFERENCES[name]["kinds"], f"{name}: the gateway changed: {new}"
        return
    old_err = [k for k in old if k.startswith("error(")]
    new_err = [k for k in new if k.startswith("error(")]
    assert new_err == old_err, f"{name}: error frames {new_err} != fixture {old_err}"


def test_write_rerecorded_fixture(live: Live, fixture_cases: dict) -> None:
    """Runs last in this module: the re-recording in the fixture's format, plus the diff."""
    missing = [n for n in CASES if n not in _recorded]
    assert not missing, f"cases not recorded: {missing}"
    base = json.loads(FIXTURE.read_text())
    out = {"description": base["description"],
           "source": {"repo": "agentcc-gateway", "commit": "live-gateway-source",
                      "recorded_by": "python/tests/gateway/live/test_live_frames.py",
                      "how": "the real gateway, its keyword guardrail and model deadline, over the mock upstream"},
           "cases": []}
    diff = {}
    for name, frames in _recorded.items():
        case = dict(fixture_cases[name])
        case["frames"] = frames
        out["cases"].append(case)
        old = [kind(f) for f in fixture_cases[name]["frames"]]
        new = [kind(f) for f in frames]
        if old != new:
            diff[name] = {"stream-fixture-source": old, "live-gateway-source": new}
    live.record("stream-error-frames.live-gateway-source", out)
    live.record("stream-error-frames.diff", {"cases_with_differences": diff,
                                             "identical_cases": [n for n in _recorded if n not in diff],
                                             "known_gateway_differences": KNOWN_GATEWAY_DIFFERENCES})
