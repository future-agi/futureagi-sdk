"""Run with the smoke-core venv (openai, anthropic, traceAI-openai / -anthropic 0.1.10); the unit tests read
its output, slimmed, from f1_requested_tools.json.

Record the span attributes the real traceAI-openai 0.1.10 / traceAI-anthropic 0.1.10 instrumentors write
for a model response that asks for a tool, with the provider HTTP answered by a canned response (no network,
no model call). Output: the unit-test fixture for F1 (tool_called's labelled fallback)."""
import json
import sys

import httpx
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

OPENAI_TOOL = {
    "id": "chatcmpl-F1fixture", "object": "chat.completion", "created": 1761170000, "model": "gpt-4.1-nano-2025-04-14",
    "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": None,
        "tool_calls": [{"id": "call_F1a", "type": "function",
                        "function": {"name": "lookup_order", "arguments": "{\"order_id\": \"A101\"}"}}]}}],
    "usage": {"prompt_tokens": 71, "completion_tokens": 17, "total_tokens": 88},
}
OPENAI_TEXT = {
    "id": "chatcmpl-F1fixture2", "object": "chat.completion", "created": 1761170001, "model": "gpt-4.1-nano-2025-04-14",
    "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant",
                                                                   "content": "Order A101 has shipped."}}],
    "usage": {"prompt_tokens": 102, "completion_tokens": 8, "total_tokens": 110},
}
ANTHROPIC_TOOL = {
    "id": "msg_F1fixture", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
    "content": [{"type": "text", "text": "Let me check."},
                {"type": "tool_use", "id": "toolu_F1a", "name": "lookup_order", "input": {"order_id": "A101"}}],
    "stop_reason": "tool_use", "stop_sequence": None, "usage": {"input_tokens": 380, "output_tokens": 54},
}
TOOLS_OPENAI = [{"type": "function", "function": {"name": "lookup_order", "description": "Look up an order by id",
                 "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}}}}]
TOOLS_ANTHROPIC = [{"name": "lookup_order", "description": "Look up an order by id",
                    "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}}}]


def spans_of(exporter):
    out = []
    for s in exporter.get_finished_spans():
        out.append({"name": s.name, "attributes": {k: (list(v) if isinstance(v, tuple) else v)
                                                   for k, v in (s.attributes or {}).items()}})
    return out


def record_openai():
    import openai
    from traceai_openai import OpenAIInstrumentor

    exp = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exp))
    OpenAIInstrumentor().instrument(tracer_provider=provider)
    answers = iter([OPENAI_TOOL, OPENAI_TEXT])
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=next(answers)))
    client = openai.OpenAI(api_key="-".join(("fixture", "openai", "placeholder")), base_url="http://fixture.invalid/v1",
                           http_client=httpx.Client(transport=transport))
    msgs = [{"role": "user", "content": "Where is order A101?"}]
    r1 = client.chat.completions.create(model="gpt-4.1-nano", messages=msgs, tools=TOOLS_OPENAI)
    msgs.append(r1.choices[0].message.model_dump(exclude_none=True))
    msgs.append({"role": "tool", "tool_call_id": "call_F1a", "content": "{\"status\": \"shipped\"}"})
    client.chat.completions.create(model="gpt-4.1-nano", messages=msgs, tools=TOOLS_OPENAI)
    OpenAIInstrumentor().uninstrument()
    return spans_of(exp)


def record_anthropic():
    import anthropic
    from traceai_anthropic import AnthropicInstrumentor

    exp = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exp))
    AnthropicInstrumentor().instrument(tracer_provider=provider)
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=ANTHROPIC_TOOL))
    client = anthropic.Anthropic(api_key="-".join(("fixture", "anthropic", "placeholder")), base_url="http://fixture.invalid",
                                 http_client=httpx.Client(transport=transport))
    client.messages.create(model="claude-haiku-5-5", max_tokens=100, tools=TOOLS_ANTHROPIC,
                           messages=[{"role": "user", "content": "Where is order A101?"}])
    AnthropicInstrumentor().uninstrument()
    return spans_of(exp)


if __name__ == "__main__":
    import importlib.metadata as md

    out = {"provenance": ("recorded by cache/l-sdk-w2b/f1/record_spans.py: the real instrumentors over canned "
                          "provider responses (httpx.MockTransport; no network, no model call)"),
           "versions": {p: md.version(p) for p in ("openai", "anthropic", "traceAI-openai", "traceAI-anthropic",
                                                     "fi-instrumentation-otel")},
           "openai_tool_loop": record_openai(), "anthropic_tool_use": record_anthropic()}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
