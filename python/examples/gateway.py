"""A tour of fi.gateway: OpenAI-compatible calls through the Agent Command Center gateway.

    export FI_GATEWAY_API_KEY=sk-agentcc-...      # a gateway key (Agent Command Center > API keys)
    export FI_GATEWAY_URL=https://gateway.futureagi.com   # or a self-hosted gateway, e.g. http://localhost:8090
    python examples/gateway.py [model] [second-provider-model]

Providers, guardrails, caching, fallbacks and budgets are configured for the org in the
control plane; every call below goes through them.
"""

from __future__ import annotations

import json
import sys
import uuid

from fi.gateway import Gateway
from fi.gateway._exceptions import APIStatusError

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gpt-4o-mini"
OTHER = sys.argv[2] if len(sys.argv) > 2 else None

gw = Gateway()


def show(r) -> None:
    m = r.agentcc
    print(f"  provider={m.provider} model={m.model_used} latency={m.latency_ms}ms cost=${m.cost} cache={m.cache_status}")


print("Models:", [m.id for m in gw.models.list().data][:10])

print("\nChat")
r = gw.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "One sentence on why LLM gateways exist."}], max_tokens=60)
print(" ", r.choices[0].message.content)
show(r)

if OTHER:
    print(f"\nSame call, another provider ({OTHER})")
    show(gw.chat.completions.create(model=OTHER, messages=[{"role": "user", "content": "Say hi"}], max_tokens=10))

print("\nStreaming")
print(" ", "".join(c.choices[0].delta.content or "" for c in gw.chat.completions.create(
    model=MODEL, messages=[{"role": "user", "content": "Count to five."}], max_tokens=30, stream=True) if c.choices))

print("\nTool call")
tools = [{"type": "function", "function": {"name": "get_weather", "parameters": {
    "type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
call = gw.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "Weather in Paris?"}], tools=tools).choices[0].message.tool_calls[0]
print(f"  {call.function.name}({json.loads(call.function.arguments)})")

print("\nA session groups calls (visible under Agent Command Center > Sessions)")
with gw.session(name="example", session_id=f"example-{uuid.uuid4().hex[:6]}") as session:
    session.step("draft")
    gw.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "Draft a haiku about routers."}], max_tokens=40)
    session.step("review")
    gw.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "Is a haiku 5-7-5?"}], max_tokens=20)
print(f"  {session.session_id}: {session.request_count} requests, {session.total_tokens} tokens, ${session.total_cost:.6f}")

print("\nErrors are typed")
try:
    gw.chat.completions.create(model="not-a-real-model", messages=[{"role": "user", "content": "hi"}])
except APIStatusError as exc:
    print(f"  {type(exc).__name__} {exc.status_code}: {exc.message}")
