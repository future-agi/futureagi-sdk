"""In-memory capture of each trial's spans for local evaluators (``trace``) and the token / cost
meter. Keyed by the trial's trace id.

Two limits per trial keep a trial's memory bounded whatever a framework puts in its spans (F7,
reports/WAVE1.md section: one trial of 2,000 spans x 16 KB raised the process by 41.8 MB):

- every captured attribute value (span or event) is cut to ``MAX_VALUE_BYTES`` (32 KB, the same limit
  as the trial's ``input.value`` / ``output.value``), ending in ``…[truncated]``;
- a trial keeps at most ``MAX_SPANS_PER_TRIAL`` spans and ``MAX_BYTES_PER_TRIAL`` (8 MiB) of span data;
  later spans are not kept, and counted. The trial's root span is always kept.

**Tokens and cost never depend on these limits** (a long agent loop passed 8 MiB and
the meter, and ``max_cost_usd``, missed a quarter of its tokens). A span past a limit that carries
usage is kept as a slim record outside the byte budget: its name, span and parent ids, model and usage
attributes only (``CapturedSpans.usage_only``). So is the parent link of a span past a limit that sits
between two such spans, so the meter's innermost-LLM-span dedup still holds. At most
``MAX_USAGE_RECORDS_PER_TRIAL`` slim records are kept; past that, the usage spans lost are counted and
said, never silently.

Nothing past a limit is silent: the trial's root span (exported with an uploaded run) carries
``fi.experiment.local_capture.*`` (see ``CaptureStats.marker``: it describes the local copy only; the
exported trace itself is not cut), the spans list handed to evaluators says how many spans were not kept
(``CapturedSpans.dropped``), trace checks that cannot find what they look for say so instead of scoring
False, and the run summary counts the trials that hit a limit.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Optional

from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor

from fi.experiments._cost import has_usage, usage_attributes

MAX_SPANS_PER_TRIAL = 2000
MAX_BYTES_PER_TRIAL = 8 * 1024 * 1024
MAX_VALUE_BYTES = 32 * 1024
MAX_USAGE_RECORDS_PER_TRIAL = 10_000  # slim usage / link records of spans past a limit (about 0.5 KB each)
MARKER = "fi.experiment.local_capture."
TRUNCATED = "…[truncated]"
_SPAN_OVERHEAD = 256  # name, ids, kind, status, times: a fixed estimate per span
_SCALAR_BYTES = 8


@dataclass
class CaptureStats:
    """What one trial's capture kept, and what it cut."""

    spans: int = 0
    bytes: int = 0
    dropped: int = 0  # spans not kept: past the span or byte limit
    truncated_values: int = 0  # attribute values cut to MAX_VALUE_BYTES
    usage_records: int = 0  # slim records kept for spans past a limit (usage, or a link between two)
    usage_lost: int = 0  # spans with usage past MAX_USAGE_RECORDS_PER_TRIAL too: not in tokens or cost
    max_spans: int = MAX_SPANS_PER_TRIAL
    max_bytes: int = MAX_BYTES_PER_TRIAL
    max_value_bytes: int = MAX_VALUE_BYTES

    @property
    def limited(self) -> bool:
        return bool(self.dropped or self.truncated_values)

    def marker(self) -> dict[str, Any]:
        """The root span's attributes for a trial whose local capture hit a limit."""
        return {
            f"{MARKER}truncated": True,
            f"{MARKER}dropped_spans": self.dropped,
            f"{MARKER}truncated_values": self.truncated_values,
            f"{MARKER}usage_records": self.usage_records,
            f"{MARKER}usage_spans_lost": self.usage_lost,
            f"{MARKER}max_spans": self.max_spans,
            f"{MARKER}max_bytes": self.max_bytes,
            f"{MARKER}max_value_bytes": self.max_value_bytes,
        }


class CapturedSpans(list):
    """A trial's captured spans (a plain list), with what the capture limits left out, and the slim
    records of spans past a limit that the token / cost meter still reads (``usage_only``)."""

    dropped: int = 0
    truncated_values: int = 0
    usage_only: list = []

    @classmethod
    def of(cls, spans: list, stats: Optional[CaptureStats], usage_only: Optional[list] = None) -> "CapturedSpans":
        out = cls(spans)
        if stats is not None:
            out.dropped, out.truncated_values = stats.dropped, stats.truncated_values
        out.usage_only = [CapturedSpan(name=n, span_id=sid, parent_id=pid, attributes=a)
                          for n, sid, pid, a in usage_only or ()]
        return out


class CapturedSpan(dict):
    """A plain, JSON-friendly view of a finished span: name, ids, kind, status, attributes,
    start/end (ns), events."""

    @property
    def name(self) -> str:
        return self["name"]

    @property
    def attributes(self) -> dict:
        return self["attributes"]


def clip(value: str, limit: int = MAX_VALUE_BYTES) -> tuple[str, int, bool]:
    """``value`` within ``limit`` UTF-8 bytes, the marker included: (text, its bytes, was it cut).
    A value the trial already cut to the limit (``input.value`` / ``output.value``) is not cut again."""
    if len(value) <= limit // 4:  # at most 4 bytes a character: fits without measuring the tail
        return value, len(value.encode("utf-8")), False
    head = value[: limit + 1].encode("utf-8")
    if len(value) <= limit and len(head) <= limit:
        return value, len(head), False
    text = head[: limit - len(TRUNCATED.encode("utf-8"))].decode("utf-8", errors="ignore") + TRUNCATED
    return text, len(text.encode("utf-8")), True


class _Clipper:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.bytes = 0
        self.truncated = 0

    def value(self, v: Any) -> Any:
        if isinstance(v, str):
            text, size, cut = clip(v, self.limit)
            self.bytes += size
            self.truncated += cut
            return text
        if isinstance(v, bytes):
            self.bytes += min(len(v), self.limit)
            if len(v) > self.limit:
                self.truncated += 1
                return v[: self.limit]
            return v
        if isinstance(v, (list, tuple)):
            return type(v)(self.value(x) for x in v)
        self.bytes += _SCALAR_BYTES
        return v

    def attributes(self, attrs: Any) -> dict:
        out = {}
        for k, v in (attrs or {}).items():
            self.bytes += len(k)
            out[k] = self.value(v)
        return out


def to_captured(span: ReadableSpan, max_value_bytes: int = MAX_VALUE_BYTES) -> tuple[CapturedSpan, int, int]:
    """(the captured view, its estimated bytes, how many values were cut)."""
    ctx = span.get_span_context()
    parent = span.parent
    c = _Clipper(max_value_bytes)
    attributes = c.attributes(span.attributes)
    events = [{"name": e.name, "attributes": c.attributes(e.attributes)} for e in span.events]
    captured = CapturedSpan(
        name=span.name,
        trace_id=format(ctx.trace_id, "032x"),
        span_id=format(ctx.span_id, "016x"),
        parent_id=format(parent.span_id, "016x") if parent else None,
        kind=str(span.kind.name) if span.kind is not None else None,
        status=str(span.status.status_code.name) if span.status is not None else None,
        attributes=attributes,
        start_ns=span.start_time,
        end_ns=span.end_time,
        events=events,
    )
    size = _SPAN_OVERHEAD + len(span.name or "") + sum(len(e.name or "") for e in span.events) + c.bytes
    return captured, size, c.truncated


class TrialCapture(SpanProcessor):
    def __init__(self, max_spans: int = MAX_SPANS_PER_TRIAL, max_bytes: int = MAX_BYTES_PER_TRIAL,
                 max_value_bytes: int = MAX_VALUE_BYTES, max_usage_records: int = MAX_USAGE_RECORDS_PER_TRIAL) -> None:
        self.max_spans = max_spans
        self.max_bytes = max_bytes
        self.max_value_bytes = max_value_bytes
        self.max_usage_records = max_usage_records
        self._lock = threading.Lock()
        self._by_trace: dict[int, list[CapturedSpan]] = {}
        self._stats: dict[int, CaptureStats] = {}
        self._slim: dict[int, list[tuple]] = {}  # (name, span id, parent id, usage attributes)
        self._needed: dict[int, set[str]] = {}  # open spans that are ancestors of a span with usage

    def open(self, trace_id: int) -> None:
        with self._lock:
            self._by_trace.setdefault(trace_id, [])
            self._slim.setdefault(trace_id, [])
            self._needed.setdefault(trace_id, set())
            self._stats.setdefault(trace_id, CaptureStats(max_spans=self.max_spans, max_bytes=self.max_bytes,
                                                          max_value_bytes=self.max_value_bytes))

    def stats(self, trace_id: int) -> Optional[CaptureStats]:
        with self._lock:
            return self._stats.get(trace_id)

    def close(self, trace_id: int) -> tuple[CapturedSpans, Optional[CaptureStats]]:
        with self._lock:
            stats = self._stats.pop(trace_id, None)
            self._needed.pop(trace_id, None)
            return CapturedSpans.of(self._by_trace.pop(trace_id, []), stats, self._slim.pop(trace_id, None)), stats

    def on_start(self, span: Any, parent_context: Optional[Any] = None) -> None:
        return None

    def _drop(self, tid: int, st: CaptureStats, span: ReadableSpan, usage: bool, link: bool) -> None:
        """A span past a limit (under the lock): counted; kept slim when the meter needs it."""
        st.dropped += 1
        if not (usage or link):
            return
        if st.usage_records >= self.max_usage_records:
            st.usage_lost += usage
            return
        parent = span.parent
        self._slim[tid].append((span.name, format(span.get_span_context().span_id, "016x"),
                                format(parent.span_id, "016x") if parent else None,
                                usage_attributes(span.attributes or {}) if usage else {}))
        st.usage_records += 1

    def on_end(self, span: ReadableSpan) -> None:
        tid = span.get_span_context().trace_id
        root = span.parent is None  # the trial's own span (a fresh trace per trial) is always kept
        usage = has_usage(span.attributes or {})
        with self._lock:
            st = self._stats.get(tid)
            if st is None:
                return
            needed = self._needed.get(tid)
            sid = format(span.get_span_context().span_id, "016x")
            link = needed is not None and sid in needed
            if link:
                needed.discard(sid)  # type: ignore[union-attr]
            if (usage or link) and needed is not None and span.parent is not None:
                needed.add(format(span.parent.span_id, "016x"))  # its ancestors must stay linked
            if not root and (st.spans >= self.max_spans or st.bytes >= self.max_bytes):
                self._drop(tid, st, span, usage, link)
                return
        captured, size, cut = to_captured(span, self.max_value_bytes)  # outside the lock: it reads the values
        with self._lock:
            st = self._stats.get(tid)
            bucket = self._by_trace.get(tid)
            if st is None or bucket is None:
                return
            if not root and (st.spans >= self.max_spans or st.bytes + size > self.max_bytes):
                self._drop(tid, st, span, usage, link)
                return
            bucket.append(captured)
            st.spans += 1
            st.bytes += size
            st.truncated_values += cut

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
