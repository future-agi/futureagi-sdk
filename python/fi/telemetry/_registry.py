"""Bounded automatic trace state; never stores spans, providers, or content."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
from time import monotonic


@dataclass
class History:
    loads: set = field(default_factory=set)
    failures: set = field(default_factory=set)
    contexts: set = field(default_factory=set)


@dataclass
class State:
    attrs: dict = field(default_factory=dict)
    history: History = field(default_factory=History)
    agent_source: str = "none"
    visible: bool = False
    _evidence: State | None = field(default=None, repr=False)
    lock: RLock = field(default_factory=RLock, repr=False)

    def view(self, mode):
        # Caller holds the owner lock through mode selection, emission and state update.
        if mode == "on":
            self.visible = True
            return self
        if self._evidence is None:
            self._evidence = State(dict(self.attrs), self.history, self.agent_source, lock=self.lock)
        return self._evidence

    def select_context(self, attrs, name):
        changed = self.attrs.get("fi.context.version_id") != attrs["fi.context.version_id"]
        self.attrs = {k: v for k, v in self.attrs.items() if not k.startswith("fi.context.")
                      and not (changed and k.startswith("fi.skills."))}
        self.attrs.update(attrs)
        if not self.attrs.get("gen_ai.agent.name") or self.agent_source == "context":
            self.attrs["gen_ai.agent.name"] = name
            self.agent_source = "context"
        self._evidence = None

    def add_skill(self, attrs):
        ids = tuple(self.attrs.get("fi.skills.version_ids", ()))
        version = attrs["fi.skill.version_id"]
        if version in ids:
            return
        if len(ids) >= 32:
            self.attrs["fi.skills.truncated"] = True
            return
        self.attrs.update({
            "fi.skills.version_ids": ids + (version,),
            "fi.skills.ids": tuple(self.attrs.get("fi.skills.ids", ())) + (attrs["fi.skill.id"],),
            "fi.skills.refs": tuple(self.attrs.get("fi.skills.refs", ())) +
                (f'{attrs["fi.skill.name"]}@v{attrs["fi.skill.version"]}',),
            "fi.skills.count": len(ids) + 1,
        })


class Registry:
    def __init__(self, capacity=4096, ttl=3600, clock=monotonic):
        self.capacity, self.ttl, self.clock = capacity, ttl, clock
        self._entries = OrderedDict()
        self._lock = RLock()

    def get(self, trace_id, *, create=False):
        """Propagation reader: private load-only traces are indistinguishable from misses."""
        state = self._lookup(trace_id, create)
        if state is not None and create:
            state.visible = True
        return state if state is not None and state.visible else None

    def owner(self, trace_id):
        return self._lookup(trace_id, True)

    def _lookup(self, trace_id, create):
        now = self.clock()
        with self._lock:
            # TTL is absolute (not renewed on read). Capacity also bounds expired
            # entries between accesses; no timer or background worker is needed.
            item = self._entries.get(trace_id)
            if item is not None and now - item[0] >= self.ttl:
                del self._entries[trace_id]
                item = None
            if item is not None:
                self._entries.move_to_end(trace_id)
                return item[1]
            if not create:
                return None
            state = State()
            self._entries[trace_id] = (now, state)
            while len(self._entries) > self.capacity:
                self._entries.popitem(last=False)
            return state


registry = Registry()
