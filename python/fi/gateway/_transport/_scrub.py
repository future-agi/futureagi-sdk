"""Remove credentials from HTTPX objects reachable through stored exchange data.

The walk follows exception args/cause/context/groups, built-in containers, instance
dictionaries and native slots, including all stored data on HTTPX requests, responses,
headers, streams, auth objects, clients and transports. It never invokes their methods,
attribute hooks, properties or caller-defined descriptors. Caller configuration dicts
are read only; only HTTPX header storage is mutated, preserving object identities.

Classes, modules, functions, frames, tracebacks, closures and other interpreter state
are outside this data boundary. Original exceptions and tracebacks remain untouched.
Credential names are masked everywhere; client-composed names are masked on requests
and standalone headers, not on a response's own gateway-provided headers. Masking is
deferred until discovery finishes so header aliases retain that provenance.

Discovery is charged before reading each root, container reference, data attribute or
slot/class-table entry. Unique queued plus processed objects never exceed NODE_CAP;
SCAN_CAP bounds discovery and DEPTH_CAP bounds path length. On a cap the frontier is
drained without expanding it, and all admitted HTTPX objects are still scrubbed.
Masking existing header rows is an in-place linear pass, not further graph discovery.
Inspection failures are counted without caller values and cannot replace an exception
already in flight.
"""
from __future__ import annotations

import builtins
import threading
import types
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from fi.gateway._constants import is_credential_name
from fi.gateway.callbacks.base import REDACTED

DEPTH_CAP = 12
NODE_CAP = 10000
SCAN_CAP = 100000

CAP_COUNTERS: dict[str, int] = {"depth": 0, "nodes": 0, "inspection_errors": 0}
"""Process-wide cap and inspection-error counters; no caller values are retained."""
_COUNTER_LOCK = threading.Lock()

_LEAVES = (str, bytes, bytearray, memoryview, bool, int, float, complex, type(None), type(Ellipsis))
_NOT_DATA = (
    type, types.ModuleType, types.FunctionType, types.MethodType, types.BuiltinFunctionType,
    types.CodeType, types.CellType, types.FrameType, types.TracebackType, types.GeneratorType,
    types.CoroutineType, types.AsyncGeneratorType, types.MethodDescriptorType,
    types.WrapperDescriptorType, types.MethodWrapperType, types.ClassMethodDescriptorType,
    types.GetSetDescriptorType, types.MemberDescriptorType, property, staticmethod, classmethod,
)
_SEQUENCES = (list, tuple, set, frozenset, deque)
_EXCEPTION_GROUP = getattr(builtins, "BaseExceptionGroup", ())
_TYPE_MRO = type.__dict__["__mro__"]
_TYPE_DICT = type.__dict__["__dict__"]


@dataclass
class ScrubReport:
    """Value-free counters for one walk, including any inspection failures."""

    visited: int = 0
    masked: int = 0
    depth_capped: int = 0
    node_capped: bool = False
    inspection_errors: int = 0
    scanned: int = 0
    pending_peak: int = 0


def _is(value: Any, classes: Any) -> bool:
    # isinstance can invoke __class__; ABC subclass checks can hash a caller class.
    # Native MRO identity checks do neither and require no virtual registrations.
    targets = classes if type(classes) is tuple else (classes,)
    return any(base is target for base in _TYPE_MRO.__get__(type(value)) for target in targets)


def _class_dicts(value: Any) -> Iterable[Any]:
    # Even a custom metaclass cannot intercept these native descriptor reads.
    for cls in _TYPE_MRO.__get__(type(value)):
        yield _TYPE_DICT.__get__(cls)


def _stored(value: Any, report: ScrubReport) -> dict[str, Any]:
    """Read only a native instance-dictionary descriptor, never a __dict__ property."""
    for namespace in _class_dicts(value):
        descriptor = namespace.get("__dict__")
        if type(descriptor) is types.GetSetDescriptorType or type(descriptor) is types.MemberDescriptorType:
            try:
                stored = descriptor.__get__(value, type(value))
                return stored if _is(stored, dict) else {}
            except BaseException:
                report.inspection_errors += 1
    return {}


def _data_attribute(value: Any, name: str, report: ScrubReport) -> Any:
    for namespace in _class_dicts(value):
        descriptor = namespace.get(name)
        if type(descriptor) is types.MemberDescriptorType:
            try:
                return descriptor.__get__(value, type(value))
            except BaseException:
                report.inspection_errors += 1
    return dict.get(_stored(value, report), name)


def _mask(headers: httpx.Headers, composed: frozenset[str], report: ScrubReport) -> int:
    """Mask native HTTPX storage without calling Headers subclass overrides."""
    masked = 0
    rows = _data_attribute(headers, "_list", report)
    if not _is(rows, list):
        return 0
    # HTTPX stores (original name, lowercase name, value) byte triples. Compact
    # masked duplicates just as Headers.__setitem__ does, without allocating a copy.
    written = 0
    private = set()
    for row in list.__iter__(rows):
        try:
            if type(row) is not tuple or len(row) != 3 or any(type(part) is not bytes for part in row):
                raise TypeError("invalid HTTPX header storage")
            original, lower, raw = row
            name = lower.decode("ascii")
            if name in composed or is_credential_name(name):
                if name in private:
                    continue
                private.add(name)
                if raw != b"[REDACTED]":
                    row = (original, lower, REDACTED.encode("ascii"))
                    masked += 1
        except BaseException:
            report.inspection_errors += 1
        list.__setitem__(rows, written, row)
        written += 1
    list.__delitem__(rows, slice(written, None))
    return masked


class _Walk:
    """Breadth-first discovery with bounded admission, not just bounded processing."""

    def __init__(self) -> None:
        self.report = ScrubReport()
        self.queue: deque[tuple[Any, int]] = deque()
        # Reserve identities when enqueueing, so cycles and repeated aliases never
        # grow the frontier. Holding the object also prevents identity reuse.
        self.seen: dict[int, Any] = {}
        self.scanned = 0
        self.sent: dict[int, httpx.Headers] = {}
        self.received: dict[int, httpx.Headers] = {}

    def charge(self, count: int = 1) -> bool:
        if self.report.node_capped:
            return False
        if self.scanned + count > SCAN_CAP:
            self.report.node_capped = True
            return False
        self.scanned += count
        self.report.scanned = self.scanned
        return True

    def take(self, iterator: Any, count: int = 1) -> Iterable[Any]:
        """Charge before advancing a known built-in (or our own) iterator."""
        while self.charge(count):
            try:
                item = next(iterator)
            except StopIteration:
                self.scanned -= count
                self.report.scanned = self.scanned
                return
            except BaseException:
                self.report.inspection_errors += 1
                return
            yield item

    def offer(self, item: Any, depth: int) -> None:
        try:
            if any(type(item) is leaf for leaf in _LEAVES) or _is(item, _NOT_DATA):
                return
            if id(item) in self.seen:
                return
            if depth > DEPTH_CAP:
                self.report.depth_capped += 1
                return
            if len(self.seen) >= NODE_CAP:
                self.report.node_capped = True
                return
            self.seen[id(item)] = item
            self.queue.append((item, depth))
            self.report.pending_peak = max(self.report.pending_peak, len(self.queue))
        except BaseException:
            self.report.inspection_errors += 1

    def _children(self, value: Any) -> Iterable[Any]:
        if _is(value, dict):
            # Charge both references before dict_items allocates its pair.
            for key, item in self.take(iter(dict.items(value)), 2):
                yield key
                yield item
        else:
            for base in _SEQUENCES:
                if _is(value, base):
                    yield from self.take(base.__iter__(value))
                    break
        if _is(value, BaseException):
            for name in ("args", "__cause__", "__context__"):
                if not self.charge():
                    return
                try:
                    child = BaseException.__dict__[name].__get__(value, type(value))
                except BaseException:
                    self.report.inspection_errors += 1
                else:
                    yield child
            if _is(value, _EXCEPTION_GROUP):
                if not self.charge():
                    return
                try:
                    child = _EXCEPTION_GROUP.__dict__["exceptions"].__get__(value, type(value))
                except BaseException:
                    self.report.inspection_errors += 1
                else:
                    yield child
        if self.report.node_capped:
            return
        yield from self.take(iter(dict.values(_stored(value, self.report))))
        # Never evaluate __slots__ as an iterable. Read the native slot descriptors,
        # charging class/attribute discovery before reading even an unset slot.
        for namespace in self.take(iter(_class_dicts(value))):
            for descriptor in self.take(iter(namespace.values())):
                if descriptor is namespace.get("__dict__"):
                    continue  # dictionary values were already discovered at this depth
                if type(descriptor) is types.MemberDescriptorType:
                    try:
                        child = descriptor.__get__(value, type(value))
                    except BaseException:
                        self.report.inspection_errors += 1
                    else:
                        yield child

    def children(self, value: Any) -> list[Any]:
        """A bounded inspection snapshot; the actual walk streams children instead."""
        found: list[Any] = []
        for child in self._children(value):
            if len(found) >= NODE_CAP:
                self.report.node_capped = True
                break
            found.append(child)
        return found

    def run(self, roots: Iterable[Any]) -> None:
        report = self.report
        # Call sites pass a list or tuple. Never execute a caller iterable protocol.
        if _is(roots, (list, tuple)):
            base = list if _is(roots, list) else tuple
            for root in self.take(base.__iter__(roots)):
                self.offer(root, 0)
        elif self.charge():
            self.offer(roots, 0)
        while self.queue:
            value, depth = self.queue.popleft()
            report.visited += 1
            # Hitting a discovery cap must not discard already-admitted objects.
            # Register their headers even after the cap, then mask them all below.
            try:
                if _is(value, (httpx.Request, httpx.Response)):
                    headers = _data_attribute(value, "headers", report)
                    if _is(headers, httpx.Headers):
                        targets = self.received if _is(value, httpx.Response) else self.sent
                        targets[id(headers)] = headers
                if _is(value, httpx.Headers):
                    self.sent[id(value)] = value
                if not report.node_capped:
                    for child in self._children(value):
                        self.offer(child, depth + 1)
                        if report.node_capped:
                            break
            except BaseException:
                report.inspection_errors += 1

    def mask(self, composed: frozenset[str]) -> None:
        for headers in self.received.values():
            try:
                self.report.masked += _mask(headers, frozenset(), self.report)
            except BaseException:
                self.report.inspection_errors += 1
        for identity, headers in self.sent.items():
            if identity not in self.received:
                try:
                    self.report.masked += _mask(headers, composed, self.report)
                except BaseException:
                    self.report.inspection_errors += 1


def scrub_reachable(roots: Iterable[Any], composed_names: frozenset[str] = frozenset()) -> ScrubReport:
    """Mask reachable HTTPX headers, preserving original errors even if inspection fails."""
    walk = _Walk()
    try:
        walk.run(roots)
    except BaseException:
        walk.report.inspection_errors += 1
    finally:
        try:
            walk.mask(composed_names)
        except BaseException:
            walk.report.inspection_errors += 1
    report = walk.report
    try:
        with _COUNTER_LOCK:
            CAP_COUNTERS["depth"] += 1 if report.depth_capped else 0
            CAP_COUNTERS["nodes"] += 1 if report.node_capped else 0
            CAP_COUNTERS["inspection_errors"] += report.inspection_errors
    except BaseException:
        report.inspection_errors += 1
    return report


def scrub_sent_request(
    request: httpx.Request | None,
    response: httpx.Response | None,
    error: BaseException | None,
    composed_names: frozenset[str] = frozenset(),
) -> None:
    """Scrub everything reachable from a send's request, response and error."""
    scrub_reachable((request, response, error), composed_names)
