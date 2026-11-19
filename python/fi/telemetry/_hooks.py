"""Public-read boundary; instrumentation exceptions never alter consumption."""
from __future__ import annotations

import sys
from contextlib import nullcontext
from contextvars import ContextVar
from time import time_ns

from . import _otel, _status
from ._identity import (
    context_attrs,
    error_type,
    identity_attrs,
    linked_attrs,
    selector_attrs,
    verified_links,
)
from ._registry import State, registry

_load_only = ContextVar("futureagi.skills.load_only", default=None)


def _state(span):
    scope = _otel._scope.get()
    if scope is not None:
        return scope
    if _otel.mode() == "load_only":
        # A single execution-context-local evidence set, not a propagation
        # registry. No current/later span attributes are changed in this mode.
        trace_id = span.get_span_context().trace_id
        entry = _load_only.get()
        if entry is None or entry[0] != trace_id:
            entry = (trace_id, State())
            _load_only.set(entry)
        return entry[1]
    return registry.get(span.get_span_context().trace_id, create=True)


def _scope_attrs(state, span):
    attrs = {}
    context = sys.modules.get("opentelemetry.context")
    value = context.get_value(_otel.CARRIER_KEY) if context else None
    if value and value.get("v") == 1:
        attrs.update(_otel.allowlisted(value.get("attrs", {})))
    if state:
        attrs.update(_otel.allowlisted(state.attrs))
    existing = getattr(span, "attributes", None) or {}
    if _otel._scope.get() is None:
        for key in ("gen_ai.agent.name", "gen_ai.agent.id"):
            if key in existing:
                attrs[key] = existing[key]
    return attrs


def _emit(name, attrs, provider, start, *, failed=False):
    if provider is None:
        return False
    trace = sys.modules["opentelemetry.trace"]
    tracer = provider.get_tracer("futureagi.context" if name == "context.load" else "futureagi.skills")
    # Identity fields have priority over optional carrier attributes at the cap.
    bounded = {}
    for key in sorted(attrs, key=lambda key: (not key.startswith("fi.skill."), key)):
        value = attrs[key]
        if isinstance(value, str):
            value = value.encode("utf-8")[:256].decode("utf-8", errors="ignore")
        elif isinstance(value, (tuple, list)):
            value = tuple(item.encode("utf-8")[:256].decode("utf-8", errors="ignore") for item in value[:32])
        bounded[key] = value
        if len(bounded) == 64:
            break
    span = tracer.start_span(name, kind=trace.SpanKind.INTERNAL, attributes=bounded, start_time=start)
    try:
        if failed:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
    finally:
        span.end()
    return True


def _enrich(state, current):
    if state is None or _otel.mode() != "on":
        return
    for key, value in state.attrs.items():
        if key.startswith("gen_ai.agent.") and key in (getattr(current, "attributes", None) or {}):
            continue
        current.set_attribute(key, value)
    if _otel._scope.get() is not None:
        _otel.publish(state)


def load_context(snapshot, state, current, provider, start, *, enrich=True):
    attrs = context_attrs(snapshot)
    if state is not None:
        version = snapshot.identity.version_id
        if version in state.contexts:
            return
        # Automatic context switches start a fresh skill list. Explicit scopes
        # are isolated at entry; never mutate another scope or an ancestor.
        if state.attrs.get("fi.context.version_id") != version:
            state.attrs = {k: v for k, v in state.attrs.items()
                           if not k.startswith(("fi.context.", "fi.skills."))}
            state.loads.clear()
        state.attrs.update(attrs)
        state.attrs.setdefault("gen_ai.agent.name", snapshot.identity.name)
        attrs.update(_scope_attrs(state, current))
    else:
        attrs.setdefault("gen_ai.agent.name", snapshot.identity.name)
    attrs["fi.context.linked_skill_version_ids"] = tuple(link["version_id"] for link in verified_links(snapshot))
    _emit("context.load", attrs, provider, start)
    if state is not None:
        state.contexts.add(version)
    if enrich:
        _enrich(state, current)


class Read:
    def __init__(self, snapshot, path=None, *, via=None, evidence="delivered", cached=False):
        self.snapshot, self.path = snapshot, path
        self.via, self.evidence, self.cached = via, evidence, cached
        self.active = False
        self.token = None

    def __enter__(self):
        try:
            if _otel.mode() == "off" or _otel._suppressed.get():
                return self
            self.current = _otel.current()
            self.provider, _ = _otel.select_provider()
            _otel.install(self.provider)
            _status.first_load()
            if self.current is None or not self.current.is_recording():
                return self
            self.state = _state(self.current)
            self.start = time_ns()
            self.active = True
            # Applies to read_all and adapter reads alike. Private verification
            # or nested public reads cannot accidentally become delivered loads.
            self.token = _otel._suppressed.set(True)
        except Exception:
            _otel.debug_failure()
        return self

    def success(self, result):
        if not self.active or _otel.mode() == "off":
            return
        try:
            snapshot = self.snapshot
            if self.path is None and snapshot.identity.kind == "agent_context":
                links = verified_links(result)
                object.__setattr__(snapshot, "_telemetry_links", links)
            self._record()
        except Exception:
            _otel.debug_failure()

    def _record(self, error=None):
        snapshot = self.snapshot
        state = self.state
        # Shared automatic traces can be used by several application threads.
        lock = state.lock if state else nullcontext()
        with lock:
            # A read (including a failed one) may have waited for transport or
            # for another reader. Off at completion forbids new evidence.
            if _otel.mode() == "off":
                return
            attrs = _scope_attrs(state, self.current)
            if snapshot.identity.kind == "agent_context" and self.path in (None, "AGENTS.md") and error is None:
                load_context(snapshot, state, self.current, self.provider, self.start)
                return
            if snapshot.identity.kind == "skill":
                skill = identity_attrs(snapshot.identity, "fi.skill")
                requested = snapshot.manifest.requested
                root = self.path in (None, "SKILL.md")
                via = self.via or ("sdk.read_all" if self.path is None else "sdk.read_file")
            else:
                linked = linked_attrs(snapshot, self.path or "")
                if linked is None:
                    # A manifest has no closure identities. Never infer a child
                    # UUID or digest from its mount name or unverified content.
                    if error is None or self.path not in (None, "AGENTS.md"):
                        return
                    skill = {"fi.skill.name": snapshot.identity.name}
                    requested, root = snapshot.manifest.requested, True
                else:
                    skill, requested, root = linked
                    attrs.update(context_attrs(snapshot))
                    attrs.setdefault("gen_ai.agent.name", snapshot.identity.name)
                    skill["fi.skill.via_context.version_id"] = snapshot.identity.version_id
                via = self.via or "context.read"
            attrs.update(selector_attrs(requested))
            attrs["fi.skill.load.via"] = via
            if error is not None:
                kind = error_type(error)
                attrs.update({"fi.skill.name": skill["fi.skill.name"], "error.type": kind})
                key = (skill["fi.skill.name"], tuple(sorted(requested.items())), kind)
                if state and key in state.failures:
                    return
                _emit("skill.load", attrs, self.provider, self.start, failed=True)
                if state:
                    state.failures.add(key)
                return
            key = (skill["fi.skill.version_id"], self.evidence)
            if state and key in state.loads:
                return
            attrs.update(skill)
            attrs.update({"fi.skill.load.evidence": self.evidence, "fi.skill.load.cached": self.cached,
                          "fi.skill.load.root_file": root})
            if snapshot.identity.kind == "skill":
                attrs["fi.skill.files"] = len(snapshot.manifest.files)
                attrs["fi.skill.bytes"] = sum(item.size_bytes for item in snapshot.manifest.files)
            if _emit("skill.load", attrs, self.provider, self.start):
                _status.recorded(attrs, self.evidence)
            if state:
                state.loads.add(key)
                if _otel.mode() == "on":
                    state.add_skill(attrs)
            _enrich(state, self.current)

    def __exit__(self, exc_type, error, tb):
        try:
            if self.active and error is not None and isinstance(error, Exception):
                self._record(error)
        except Exception:
            _otel.debug_failure()
        finally:
            if self.token is not None:
                _otel._suppressed.reset(self.token)
        return False


def declare_skill(snapshot_or_lock_entry):
    if _otel.mode() == "off":
        return
    try:
        from types import SimpleNamespace

        from fi.context.materialize import LockedLink
        from fi.context.snapshot import SnapshotIdentity
        snapshot = snapshot_or_lock_entry
        via = "explicit"
        if isinstance(snapshot, LockedLink):
            link = snapshot
            snapshot = SimpleNamespace(
                identity=SnapshotIdentity("skill", link.skill_id, link.mount.split("/")[1],
                                          link.version, link.version_id, link.digest),
                manifest=SimpleNamespace(requested=link.requested.model_dump(exclude_none=True), files=()),
            )
            via = "lock"
        if snapshot.identity.kind != "skill":
            return
        with Read(snapshot, via=via, evidence="declared", cached=True) as read:
            read.success(snapshot)
    except Exception:
        _otel.debug_failure()
