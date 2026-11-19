"""Public-read boundary; instrumentation exceptions never alter consumption."""
from __future__ import annotations

import sys
from time import time_ns

from . import _agent_name, _otel, _status
from ._identity import (
    context_attrs,
    error_type,
    identity_attrs,
    linked_attrs,
    selector_attrs,
    verified_links,
)
from ._registry import registry

_EMPTY_CARRIER = _otel.carrier({})


def _scope_attrs(state, span, *, linked_context=None):
    attrs = {}
    context = sys.modules.get("opentelemetry.context")
    value = context.get_value(_otel.CARRIER_KEY) if context else None
    if _otel._scope.get() is None and value and value.get("v") == 1:
        attrs.update(_otel.allowlisted(value.get("attrs", {})))
        if "fi.context.version_id" in state.attrs:
            # A verified context replaces its entire identity. Do not recover a
            # prior context's optional receipt or selector from an older carrier.
            attrs = {k: v for k, v in attrs.items() if not k.startswith(("fi.context.", "fi.skills."))}
    attrs.update(_otel.allowlisted(state.attrs))
    if linked_context is not None:
        # Build evidence for the actual file source, not the prior selection.
        # A linked read does not itself change the trace's standing context.
        attrs = {k: v for k, v in attrs.items() if not k.startswith(("fi.context.", "fi.skills."))}
        attrs.update(context_attrs(linked_context))
        if _agent_name.NAME not in attrs or state.agent_source == "context":
            attrs[_agent_name.NAME] = linked_context.identity.name
    existing = getattr(span, "attributes", None) or {}
    if _otel._scope.get() is None:
        for key in ("gen_ai.agent.name", "gen_ai.agent.id"):
            if key in existing and not (key == "gen_ai.agent.name" and _agent_name.automatic(span)):
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
    # The complete selected view is already in bounded. Prevent an on-start
    # processor from backfilling omitted fields from a previous context.
    context = sys.modules["opentelemetry.context"]
    parent = context.set_value(_otel.CARRIER_KEY, _EMPTY_CARRIER)
    span = tracer.start_span(name, context=parent, kind=trace.SpanKind.INTERNAL, attributes=bounded, start_time=start)
    try:
        if not span.is_recording():
            return False
        if failed:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
    finally:
        span.end()
    return True


def _enrich(state, current, mode, *, reset_skills=False):
    if mode != "on":
        return
    if _otel._scope.get() is not None:
        # The active span can be an ancestor shared by concurrent explicit scopes.
        _otel.publish(state)
        return
    existing = getattr(current, "attributes", None) or {}
    if reset_skills and "fi.skills.count" in existing:
        # OTel cannot delete an attribute. Clear the former context's skill
        # list on the already-enriched span, not on unrelated future children.
        for key in ("fi.skills.version_ids", "fi.skills.ids", "fi.skills.refs"):
            current.set_attribute(key, ())
        current.set_attribute("fi.skills.count", 0)
        if "fi.skills.truncated" in existing:
            current.set_attribute("fi.skills.truncated", False)
    for key, value in state.attrs.items():
        if key.startswith("gen_ai.agent.") and key in existing and not (
            key == "gen_ai.agent.name" and _agent_name.automatic(current)
        ):
            continue
        if key == _agent_name.NAME and state.agent_source == "context":
            _agent_name.write_context_name(current, value)
        else:
            current.set_attribute(key, value)


def load_context(snapshot, state, current, provider, start, mode, *, enrich=True):
    attrs = context_attrs(snapshot)
    version = snapshot.identity.version_id
    changed = state.attrs.get("fi.context.version_id") != version
    state.select_context(attrs, snapshot.identity.name)
    if version not in state.history.contexts:
        attrs = {**_scope_attrs(state, current), **attrs}
        attrs["fi.context.linked_skill_version_ids"] = tuple(link["version_id"] for link in verified_links(snapshot))
        if _emit("context.load", attrs, provider, start):
            state.history.contexts.add(version)
    if enrich:
        _enrich(state, current, mode, reset_skills=changed)


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
            self.scope = _otel._scope.get()
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
        if _otel.mode() == "off":
            return
        owner = self.scope or registry.owner(self.current.get_span_context().trace_id)
        with owner.lock:
            mode = _otel.mode()
            if mode == "off":
                return
            state = owner.view(mode)
            if mode == "on":
                _otel.install(self.provider)
            linked_context = None
            if snapshot.identity.kind == "agent_context" and self.path in (None, "AGENTS.md") and error is None:
                load_context(snapshot, state, self.current, self.provider, self.start, mode)
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
                    linked_context = snapshot
                    skill["fi.skill.via_context.version_id"] = snapshot.identity.version_id
                via = self.via or "context.read"
            attrs = _scope_attrs(state, self.current, linked_context=linked_context)
            attrs.update(selector_attrs(requested))
            attrs["fi.skill.load.via"] = via
            if error is not None:
                kind = error_type(error)
                attrs.update({"fi.skill.name": skill["fi.skill.name"], "error.type": kind})
                key = (skill["fi.skill.name"], tuple(sorted(requested.items())), kind)
                if key in state.history.failures:
                    return
                if _emit("skill.load", attrs, self.provider, self.start, failed=True):
                    state.history.failures.add(key)
                return
            key = (skill["fi.skill.version_id"], self.evidence)
            attrs.update(skill)
            attrs.update({"fi.skill.load.evidence": self.evidence, "fi.skill.load.cached": self.cached,
                          "fi.skill.load.root_file": root})
            if snapshot.identity.kind == "skill":
                attrs["fi.skill.files"] = len(snapshot.manifest.files)
                attrs["fi.skill.bytes"] = sum(item.size_bytes for item in snapshot.manifest.files)
            if key not in state.history.loads and _emit("skill.load", attrs, self.provider, self.start):
                state.history.loads.add(key)
                _status.recorded(attrs, self.evidence)
            if mode == "on":
                state.add_skill(attrs)
                _enrich(state, self.current, mode)

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
