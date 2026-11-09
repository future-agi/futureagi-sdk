"""Content controls must apply to serialized exports, not just processor logs."""

import io
import json
import socket

import httpx
import pytest


MARKER = "PRIVATE_MARKER"
PROMPT = "gen_ai.prompt.0.content"
COMPLETION = "gen_ai.completion.0.content"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("network is forbidden in tracing content tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setenv("FI_API_KEY", "test-only")
    monkeypatch.setenv("FI_SECRET_KEY", "test-only")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")


@pytest.fixture
def exports(monkeypatch):
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter as grpc
    from opentelemetry.exporter.otlp.proto.http import trace_exporter as http
    from opentelemetry.sdk.trace import SpanProcessor
    from opentelemetry.sdk.trace import export
    from fi.evals.otel import tracer

    console = io.StringIO()
    console_type = export.ConsoleSpanExporter
    records = {"grpc": [], "http": []}
    payloads = {"grpc": [], "http": []}
    stopped = []
    originals = []
    providers = []

    class RecordingExporter(export.SpanExporter):
        def __init__(self, kind):
            self.kind = kind

        def export(self, spans):
            records[self.kind].extend(spans)
            payloads[self.kind].append(encode_spans(spans).SerializeToString())
            return export.SpanExportResult.SUCCESS

        def shutdown(self):
            stopped.append(self.kind)

    class OriginalSpans(SpanProcessor):
        def on_end(self, span):
            originals.append(span)

    monkeypatch.setattr(export, "ConsoleSpanExporter", lambda: console_type(out=console))
    monkeypatch.setattr(grpc, "OTLPSpanExporter", lambda **kwargs: RecordingExporter("grpc"))
    monkeypatch.setattr(http, "OTLPSpanExporter", lambda **kwargs: RecordingExporter("http"))
    # Keep this provider local: other tests and applications may already have a global one.
    monkeypatch.setattr(trace, "set_tracer_provider", lambda provider: providers.append(provider))
    monkeypatch.setattr(tracer, "_tracer_provider", None)
    monkeypatch.setattr(tracer, "_is_initialized", False)
    # Recent SDKs added this no-op lifecycle hook. Isolate that unrelated
    # compatibility issue while retaining the real enrichment on_end callback.
    if hasattr(SpanProcessor, "_on_ending"):
        monkeypatch.setattr(tracer.CompositeSpanProcessor, "_on_ending",
                            SpanProcessor._on_ending, raising=False)

    def start(content=None, *, processors=None, from_kwargs=False):
        from fi.evals.otel import (
            CostConfig, EvaluationConfig, ExporterConfig, ExporterType,
            TraceConfig, setup_tracing,
        )

        options = dict(
            exporters=[ExporterConfig(type=kind) for kind in (
                ExporterType.CONSOLE, ExporterType.OTLP_GRPC, ExporterType.OTLP_HTTP,
            )],
            evaluation=EvaluationConfig(enabled=False),
            cost=CostConfig(enabled=False),
        )
        if content is not None:
            options["content"] = content
        if processors is not None:
            options["processors"] = processors
        if from_kwargs:
            # The environment-style entry point creates its own exporter list.
            options.pop("exporters")
            provider = setup_tracing(otlp_endpoint="http://collector.invalid:4317", **options)
        else:
            provider = setup_tracing(TraceConfig(**options))
        provider.add_span_processor(OriginalSpans())
        return provider

    yield start, console, records, payloads, originals, stopped
    for provider in providers:
        provider.shutdown()


def _call_openai(monkeypatch, provider):
    import openai
    from fi.evals.otel import OpenAIInstrumentor

    def reply(request):
        assert MARKER in request.content.decode()
        return httpx.Response(200, json={
            "id": "chat-test", "object": "chat.completion", "created": 0,
            "model": "test-model", "usage": {
                "prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3,
            },
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": "reply " + MARKER,
            }}],
        })

    instrumentor = OpenAIInstrumentor()
    monkeypatch.setattr(instrumentor, "get_tracer", lambda: provider.get_tracer("test-provider"))
    instrumentor.instrument()
    try:
        assert instrumentor.is_instrumented
        with openai.OpenAI(
            api_key="test-only", base_url="https://provider.invalid/v1", max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(reply), trust_env=False),
        ) as client:
            response = client.chat.completions.create(
                model="test-model", messages=[{"role": "user", "content": "prompt " + MARKER}],
            )
            # Export policy must not modify the response returned to the application.
            assert response.choices[0].message.content == "reply " + MARKER
    finally:
        instrumentor.uninstrument()
    assert provider.force_flush()


@pytest.mark.parametrize("capture_prompts,capture_completions", [
    (True, True), (False, True), (True, False), (False, False),
])
def test_instrumented_content_is_sanitized_in_every_export(
    monkeypatch, exports, capture_prompts, capture_completions,
):
    from fi.evals.otel import ContentConfig

    start, console, records, payloads, originals, _ = exports
    provider = start(ContentConfig(
        capture_prompts=capture_prompts, capture_completions=capture_completions,
        redact_patterns=[MARKER],
    ))
    _call_openai(monkeypatch, provider)

    document = json.loads(console.getvalue())
    assert MARKER not in console.getvalue()
    exported = [document["attributes"]]
    for kind in records:
        assert len(records[kind]) == 1
        assert len(payloads[kind]) == 1
        assert MARKER.encode() not in payloads[kind][0]
        exported.append(dict(records[kind][0].attributes))
    for attributes in exported:
        assert (PROMPT in attributes) is capture_prompts
        assert (COMPLETION in attributes) is capture_completions
        if capture_prompts:
            assert attributes[PROMPT] == "[user]: prompt [REDACTED]"
        if capture_completions:
            assert attributes[COMPLETION] == "reply [REDACTED]"
        assert attributes["gen_ai.request.model"] == "test-model"
        assert attributes["gen_ai.usage.total_tokens"] == 3
    assert len(originals) == 1
    assert MARKER in originals[0].attributes[PROMPT]
    assert MARKER in originals[0].attributes[COMPLETION]


@pytest.mark.parametrize("capture_prompts,capture_completions", [
    (False, True), (True, False), (False, False),
])
def test_disabled_capture_removes_all_supported_content_without_regex(
    exports, capture_prompts, capture_completions,
):
    from fi.evals.otel import ContentConfig

    prompt_keys = [PROMPT, "gen_ai.prompt.12.content", "gen_ai.input.messages",
                   "gen_ai.system_instructions", "llm.prompt", "prompt", "input",
                   "llm.messages", "messages"]
    completion_keys = [COMPLETION, "gen_ai.completion.12.content", "gen_ai.output.messages",
                       "llm.completion", "completion", "output", "response",
                       "llm.choices", "choices"]
    attributes = dict.fromkeys(prompt_keys + completion_keys, MARKER)
    attributes.update({"gen_ai.prompt.0.role": "user", "gen_ai.usage.input_tokens": 7})
    start, console, records, _, _, _ = exports
    # Privacy must not depend on the optional enrichment processor being enabled.
    provider = start(ContentConfig(
        capture_prompts=capture_prompts, capture_completions=capture_completions,
    ), processors=[])
    with provider.get_tracer("test").start_as_current_span("chat", attributes=attributes):
        pass
    assert provider.force_flush()
    exported = [json.loads(console.getvalue())["attributes"]]
    exported.extend(dict(spans[0].attributes) for spans in records.values())
    for values in exported:
        for keys, captured in ((prompt_keys, capture_prompts), (completion_keys, capture_completions)):
            for key in keys:
                assert (key in values) is captured
                if captured:
                    assert values[key] == MARKER
        assert values["gen_ai.prompt.0.role"] == "user"
        assert values["gen_ai.usage.input_tokens"] == 7


def test_redaction_handles_message_json_and_sequences_and_preserves_span_metadata(exports):
    from opentelemetry.trace import Link, SpanContext, SpanKind, Status, StatusCode, TraceFlags
    from fi.evals.otel import ContentConfig

    start, console, records, payloads, originals, _ = exports
    provider = start(ContentConfig(redact_patterns=[r"PRIVATE_[A-Z]+", r"SECOND_\d+"]))
    context = SpanContext(1, 2, False, TraceFlags(1))
    attributes = {
        "gen_ai.input.messages": json.dumps([{"role": "user", "content": MARKER}]),
        "gen_ai.output.messages": ("reply " + MARKER, "SECOND_123"),
        "gen_ai.prompt.3.content": MARKER,
        "gen_ai.completion.2.content": MARKER,
        "gen_ai.system_instructions": MARKER,
        "custom.count": 9,
    }
    with provider.get_tracer("test-scope", "1.2.3").start_as_current_span(
        "chat", kind=SpanKind.CLIENT, attributes=attributes, links=[Link(context)],
    ) as span:
        span.add_event("completed", {"tokens": 3})
        span.set_status(Status(StatusCode.OK))
    assert provider.force_flush()
    assert MARKER not in console.getvalue()
    for kind, spans in records.items():
        assert MARKER.encode() not in payloads[kind][0]
        assert b"SECOND_123" not in payloads[kind][0]
        result = spans[0]
        assert json.loads(result.attributes["gen_ai.input.messages"])[0]["content"] == "[REDACTED]"
        assert tuple(result.attributes["gen_ai.output.messages"]) == ("reply [REDACTED]", "[REDACTED]")
        assert result.attributes["custom.count"] == 9
        for name in ("name", "context", "parent", "kind", "status", "start_time", "end_time",
                     "resource", "events", "links", "instrumentation_scope", "dropped_attributes"):
            assert getattr(result, name) == getattr(originals[0], name)
    assert originals[0].attributes["gen_ai.prompt.3.content"] == MARKER


def test_kwargs_configuration_is_scoped_to_each_provider(exports):
    from fi.evals.otel import ContentConfig

    start, _, records, _, _, _ = exports
    private = start(ContentConfig(redact_patterns=[MARKER]), from_kwargs=True)
    unchanged = start(ContentConfig(), from_kwargs=True)
    for provider in (private, unchanged):
        with provider.get_tracer("test").start_as_current_span("chat", attributes={PROMPT: MARKER}):
            pass
        assert provider.force_flush()
    assert [span.attributes[PROMPT] for span in records["grpc"]] == ["[REDACTED]", MARKER]
    assert records["http"] == []


def test_content_is_redacted_before_configured_truncation_and_exporters_shutdown(exports):
    from fi.evals.otel import ContentConfig

    start, _, records, _, _, stopped = exports
    provider = start(ContentConfig(redact_patterns=[MARKER], max_content_length=12))
    with provider.get_tracer("test").start_as_current_span(
        "chat", attributes={PROMPT: "prefix " + MARKER + " trailing text"},
    ):
        pass
    assert provider.force_flush()
    for spans in records.values():
        assert spans[0].attributes[PROMPT] == "prefix [REDA... [truncated]"
    provider.shutdown()
    assert sorted(stopped) == ["grpc", "http"]


@pytest.mark.parametrize("from_kwargs", [False, True], ids=["config", "kwargs"])
@pytest.mark.parametrize("explicit_defaults", [False, True], ids=["omitted", "default"])
def test_default_content_preserves_exported_span_bytes(exports, from_kwargs, explicit_defaults):
    from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
    from fi.evals.otel import ContentConfig

    start, console, records, payloads, originals, _ = exports
    content = ContentConfig() if explicit_defaults else None
    provider = start(content, processors=[], from_kwargs=from_kwargs)
    long_text = "x" * (ContentConfig().max_content_length + 1) + MARKER
    attributes = {
        PROMPT: long_text,
        COMPLETION: "reply " + long_text,
        "gen_ai.input.messages": (long_text, "short"),
        "gen_ai.output.messages": ("short", long_text),
        "gen_ai.system_instructions": "λ" + long_text,
        "gen_ai.prompt.0.role": "user",
        "custom.count": 9,
    }
    with provider.get_tracer("test-scope", "1.2.3").start_as_current_span(
        "manual-chat", attributes=attributes,
    ) as span:
        span.add_event("completed", {"tokens": 3})
    assert provider.force_flush()
    assert len(originals) == 1
    original = originals[0]
    assert dict(original.attributes) == attributes
    expected_payload = encode_spans([original]).SerializeToString()
    if from_kwargs:
        assert console.getvalue() == ""
        assert records["http"] == payloads["http"] == []
        kinds = ("grpc",)
    else:
        assert console.getvalue().encode() == (original.to_json() + "\n").encode()
        kinds = ("grpc", "http")
    for kind in kinds:
        assert len(records[kind]) == 1
        assert records[kind][0] is original
        assert payloads[kind] == [expected_payload]


@pytest.mark.parametrize("limit", [12, 10001])
def test_non_default_content_length_without_other_controls_is_applied(exports, limit):
    from fi.evals.otel import ContentConfig

    start, console, records, payloads, originals, _ = exports
    provider = start(ContentConfig(max_content_length=limit), processors=[])
    text = "x" * (limit + 1)
    with provider.get_tracer("test").start_as_current_span(
        "manual-chat", attributes={PROMPT: text, COMPLETION: text},
    ):
        pass
    assert provider.force_flush()
    expected = "x" * limit + "... [truncated]"
    exported = [json.loads(console.getvalue())["attributes"]]
    for kind, spans in records.items():
        assert len(spans) == 1
        assert expected.encode() in payloads[kind][0]
        exported.append(dict(spans[0].attributes))
    for attributes in exported:
        assert attributes[PROMPT] == attributes[COMPLETION] == expected
    assert originals[0].attributes[PROMPT] == originals[0].attributes[COMPLETION] == text
