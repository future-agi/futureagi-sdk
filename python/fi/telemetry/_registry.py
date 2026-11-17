"""Bounded automatic trace state; never stores spans, providers, or content."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
from time import monotonic


@dataclass
class State:
    attrs: dict = field(default_factory=dict)
    loads: set = field(default_factory=set)
    failures: set = field(default_factory=set)
    contexts: set = field(default_factory=set)
    lock: RLock = field(default_factory=RLock, repr=False)

    def child(self, *, reset=False):
        # A child has its own load evidence and lists, never mutates its parent.
        return State(attrs={} if reset else dict(self.attrs))

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
