"""``tracing_env`` and ``context_from_env``: TRACEPARENT / TRACESTATE only by default, each opt-in key
only through its own argument, with credential names excluded, no trace keys without OpenTelemetry, and a
round trip through the environment that lands on the same span. OpenTelemetry's own SDK is used where
it is installed (the CI full suite has it through ``gateway-otel``); those tests skip without it. No
test touches the global tracer provider."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote

import pytest

from fi.sandbox import ConfigurationError
from fi.sandbox_integrations.tracing import REFUSED_ENV_NAMES, context_from_env, tracing_env

PYTHON = Path(__file__).resolve().parents[2]
TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
REFUSED = ("FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "FI_PLATFORM_TOKEN", "OMEGA_OS_API_KEY")
#: Synthetic test values only.
ENVIRON = {
    "FI_BASE_URL": "https://collector.example.test",
    "FI_PROJECT_NAME": "from-environ",
    "FI_PROJECT_VERSION_NAME": "v-from-environ",
    "FI_HIDE_INPUTS": "true",
    "FI_HIDE_OUTPUT_MESSAGES": "1",
    "FI_PII_REDACTION": "true",
    "OTEL_RESOURCE_ATTRIBUTES": "from=environ",
    "BAGGAGE": "from=environ",
    **dict.fromkeys(REFUSED, "fake-value-0000"),
}


@pytest.fixture
def otel():
    """A tracer from a private provider and the OpenTelemetry modules the tests use."""
    pytest.importorskip("opentelemetry.sdk")
    from opentelemetry import baggage, context, trace
    from opentelemetry.sdk.trace import TracerProvider

    tracer = TracerProvider().get_tracer("tests.sandbox_integrations")
    return SimpleNamespace(trace=trace, baggage=baggage, context=context, tracer=tracer)


def ids(span) -> tuple:
    sc = span.get_span_context()
    return format(sc.trace_id, "032x"), format(sc.span_id, "016x")


def test_no_opentelemetry_gives_no_trace_keys(monkeypatch):
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    assert tracing_env(environ=ENVIRON) == {}
    # the opt-ins do not need OpenTelemetry, and still carry no trace key
    out = tracing_env(baggage=True, collector=True, environ=ENVIRON)
    assert out == {"FI_BASE_URL": ENVIRON["FI_BASE_URL"]}
    with pytest.raises(ImportError, match="opentelemetry-api"):
        context_from_env({"TRACEPARENT": "00-" + "1" * 32 + "-" + "2" * 16 + "-01"})


def test_no_span_gives_no_trace_keys(otel):
    assert tracing_env(environ={}) == {}
    invalid = otel.trace.INVALID_SPAN
    assert tracing_env(span=invalid, environ={}) == {}


def test_traceparent_format_and_names_active_span(otel):
    with otel.tracer.start_as_current_span("caller") as span:
        out = tracing_env(environ={})
    assert set(out) == {"TRACEPARENT"}  # a fresh span carries no trace state
    match = TRACEPARENT.match(out["TRACEPARENT"])
    assert match, out["TRACEPARENT"]
    assert (match.group(1), match.group(2)) == ids(span)
    # The trace flags: any byte (W3C level 2 adds random-trace-id, 0x02, beside sampled, 0x01), copied
    # directly from the span, including the span's sampled bit.
    flags = int(match.group(3), 16)
    assert flags == int(span.get_span_context().trace_flags)
    assert bool(flags & 0x01) == span.get_span_context().trace_flags.sampled


def test_explicit_span_argument_wins(otel):
    other = otel.tracer.start_span("other")
    try:
        with otel.tracer.start_as_current_span("current") as current:
            out = tracing_env(span=other, environ={})
        match = TRACEPARENT.match(out["TRACEPARENT"])
        assert (match.group(1), match.group(2)) == ids(other)
        assert (match.group(1), match.group(2)) != ids(current)
    finally:
        other.end()


def test_tracestate_present_when_the_span_carries_it(otel):
    from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState

    sc = SpanContext(
        trace_id=0x1234, span_id=0x5678, is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED), trace_state=TraceState([("fi", "1"), ("vendor", "x")]),
    )
    out = tracing_env(span=NonRecordingSpan(sc), environ={})
    assert out == {"TRACEPARENT": f"00-{0x1234:032x}-{0x5678:016x}-01", "TRACESTATE": "fi=1,vendor=x"}


def test_trace_flags_pass_through_unchanged(otel):
    from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

    # Flag bits other than sampled (here random-trace-id, 0x02) are neither dropped nor rewritten.
    for value in (0x00, 0x01, 0x02, 0x03):
        sc = SpanContext(trace_id=0x1234, span_id=0x5678, is_remote=False, trace_flags=TraceFlags(value))
        out = tracing_env(span=NonRecordingSpan(sc), environ={})
        assert out == {"TRACEPARENT": f"00-{0x1234:032x}-{0x5678:016x}-{value:02x}"}


def test_default_is_traceparent_and_tracestate_only(otel):
    token = otel.context.attach(otel.baggage.set_baggage("tenant", "acme"))
    try:
        with otel.tracer.start_as_current_span("caller"):
            out = tracing_env(environ=ENVIRON)
            with_state = tracing_env(span=_span_with_state(), environ=ENVIRON)
    finally:
        otel.context.detach(token)
    assert set(out) == {"TRACEPARENT"}
    assert set(with_state) == {"TRACEPARENT", "TRACESTATE"}
    for result in (out, with_state):
        assert "BAGGAGE" not in result and "OTEL_RESOURCE_ATTRIBUTES" not in result
        assert not [name for name in result if name.startswith("FI_")]
        assert not [value for value in result.values() if "sandbox.id" in value]


def _span_with_state():
    from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState

    return NonRecordingSpan(SpanContext(
        trace_id=0xABC, span_id=0xDEF, is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED), trace_state=TraceState([("fi", "1")]),
    ))


def test_never_contains_refused_names_even_when_in_environ(otel):
    assert set(REFUSED) == set(REFUSED_ENV_NAMES)
    with otel.tracer.start_as_current_span("caller"):
        everything = tracing_env(
            baggage=True, collector=True, project_name="p", project_version_name="v",
            privacy_flags=True, resource_attributes={"a": "b"}, environ=ENVIRON,
        )
    assert not set(everything) & set(REFUSED)
    assert "fake-value-0000" not in json.dumps(everything)


def test_opt_in_keys_off_by_default_and_each_adds_only_its_own(otel):
    token = otel.context.attach(otel.baggage.set_baggage("tenant", "acme"))
    try:
        with otel.tracer.start_as_current_span("caller"):
            base = tracing_env(environ=ENVIRON)
            added = {
                "baggage": tracing_env(baggage=True, environ=ENVIRON),
                "collector": tracing_env(collector=True, environ=ENVIRON),
                "project_name": tracing_env(project_name="checkout-agent", environ=ENVIRON),
                "project_version_name": tracing_env(project_version_name="v2", environ=ENVIRON),
                "privacy_flags": tracing_env(privacy_flags=True, environ=ENVIRON),
                "resource_attributes": tracing_env(
                    resource_attributes={"service.name": "job", "team": "a,b=c d/é"}, environ=ENVIRON
                ),
            }
    finally:
        otel.context.detach(token)
    assert set(base) == {"TRACEPARENT"}

    def extra(name):
        out = added[name]
        assert out["TRACEPARENT"] == base["TRACEPARENT"]
        return {k: v for k, v in out.items() if k not in base}

    assert extra("baggage") == {"BAGGAGE": "tenant=acme"}
    assert extra("collector") == {"FI_BASE_URL": "https://collector.example.test"}
    assert extra("project_name") == {"FI_PROJECT_NAME": "checkout-agent"}  # the argument, not environ
    assert extra("project_version_name") == {"FI_PROJECT_VERSION_NAME": "v2"}
    assert extra("privacy_flags") == {
        "FI_HIDE_INPUTS": "true", "FI_HIDE_OUTPUT_MESSAGES": "1", "FI_PII_REDACTION": "true",
    }
    joined = extra("resource_attributes")["OTEL_RESOURCE_ATTRIBUTES"]
    pairs = [pair.split("=", 1) for pair in joined.split(",")]
    assert [key for key, _ in pairs] == ["service.name", "team"]
    assert {key: unquote(value) for key, value in pairs} == {"service.name": "job", "team": "a,b=c d/é"}
    assert set(extra("resource_attributes")) == {"OTEL_RESOURCE_ATTRIBUTES"}


def test_collector_without_fi_base_url_adds_nothing():
    assert tracing_env(collector=True, environ={}) == {}


@pytest.mark.parametrize("bad", ["", "a,b", "a=b", "a b"])
def test_resource_attribute_name_must_be_plain(bad):
    with pytest.raises(ConfigurationError) as caught:
        tracing_env(resource_attributes={bad: "x"}, environ={})
    assert caught.value.code == "invalid_option"


def test_context_from_env_round_trip(otel):
    token = otel.context.attach(otel.baggage.set_baggage("tenant", "acme"))
    try:
        with otel.tracer.start_as_current_span("caller") as caller:
            env = tracing_env(baggage=True, environ={})
    finally:
        otel.context.detach(token)
    ctx = context_from_env(env)
    parent = otel.trace.get_current_span(ctx).get_span_context()
    assert parent.is_valid and parent.is_remote
    assert (format(parent.trace_id, "032x"), format(parent.span_id, "016x")) == ids(caller)
    assert otel.baggage.get_baggage("tenant", ctx) == "acme"
    # a span started under that context is a child of the caller's span
    with otel.tracer.start_as_current_span("in-sandbox", context=ctx) as child:
        assert child.get_span_context().trace_id == caller.get_span_context().trace_id
        assert child.parent.span_id == caller.get_span_context().span_id
    # trace state survives the trip too
    state = context_from_env(tracing_env(span=_span_with_state(), environ={}))
    assert otel.trace.get_current_span(state).get_span_context().trace_state.get("fi") == "1"


def test_context_from_env_without_traceparent_is_empty(otel):
    for environ in ({}, {"TRACEPARENT": "not-a-traceparent"}):
        assert not otel.trace.get_current_span(context_from_env(environ)).get_span_context().is_valid


def test_importing_the_tracing_package_loads_no_opentelemetry():
    code = (
        f"import sys; sys.path.insert(0, {str(PYTHON)!r})\n"
        "import fi.sandbox_integrations.tracing\n"
        "import json; print(json.dumps(sorted(sys.modules)))"
    )
    out = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True, timeout=120, cwd=str(PYTHON)
    )
    assert out.returncode == 0, out.stderr
    loaded = json.loads(out.stdout)
    assert not [m for m in loaded if m == "opentelemetry" or m.startswith("opentelemetry.")]
