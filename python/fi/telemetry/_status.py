"""Content-free, credential-free diagnostics for optional runtime tracing."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from . import _otel

RULE = "A load is recorded on the first read of any file of a skill version inside a trace"
_logged = set()
_last_load = None


def status():
    provider, source = _otel.select_provider()
    mode = _otel.mode()
    installed = bool(mode == "on" and getattr(provider, "_futureagi_skills_processor", False))
    scope = _otel._scope.get()
    span = _otel.current()
    attrs = dict(getattr(span, "attributes", None) or {})
    if scope:
        attrs.update(scope.attrs)
    agent = attrs.get("gen_ai.agent.name")
    agent_source = "agent_scope" if agent and scope else "framework" if agent else "none"
    if not agent and attrs.get("fi.context.name"):
        agent, agent_source = attrs["fi.context.name"], "context"
    if agent and scope and getattr(scope, "agent_source", None):
        agent_source = scope.agent_source
    if not agent:
        resource = getattr(provider, "resource", None)
        service = (getattr(resource, "attributes", None) or {}).get("service.name")
        if service and not service.startswith("unknown_service"):
            agent, agent_source = service, "service.name"
    row = "OTel absent / no provider"
    if source == "traceai":
        row = "Python traceAI register()"
    elif source in ("global", "configured"):
        row = "Python vanilla OTel SDK TracerProvider, global" if source == "global" else "Python configured provider"
    elif span is not None and span.is_recording():
        row = "Python vanilla, non-global provider, not passed to configure"
    return {
        "otel_found": sys.modules.get("opentelemetry.trace") is not None,
        "provider": source, "processor_installed": installed, "mode": mode,
        "truth_table_row": row, "agent_name": agent, "agent_name_source": agent_source,
        "rule": RULE, "last_load": dict(_last_load) if _last_load else None,
    }


def first_load():
    if _otel.mode() == "off":
        return
    facts = status()
    if not facts["otel_found"]:
        message = "no OpenTelemetry in this process"
    elif facts["provider"] == "none":
        message = "no tracer provider found: pass one to fi.telemetry.configure(tracer_provider=…)"
    else:
        message = (f'recording skill loads (provider: {facts["provider"]}; '
                   f'later spans: {"stamped" if facts["processor_installed"] else "not stamped"}; '
                   f'agent name source: {facts["agent_name_source"]}. '
                   'Set agent_scope(agent=…) or OTEL_SERVICE_NAME)')
    if message not in _logged:
        _logged.add(message)
        logging.getLogger("futureagi.telemetry").info("futureagi: %s", message)


def recorded(attrs, evidence):
    global _last_load
    _last_load = {"skill_name": attrs["fi.skill.name"], "version": attrs["fi.skill.version"],
                  "evidence": evidence, "time": datetime.now(timezone.utc).isoformat()}
