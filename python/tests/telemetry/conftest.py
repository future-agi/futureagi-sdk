"""Synthetic verified bytes; OTel is imported only by the tracing fixture."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

SKILL_ID = "11111111-1111-4111-8111-111111111111"
VERSION_ID = "22222222-2222-4222-8222-222222222222"
CONTEXT_ID = "33333333-3333-4333-8333-333333333333"
CONTEXT_VERSION = "44444444-4444-4444-8444-444444444444"


def digest(files):
    pairs = sorted((path, hashlib.sha256(text.encode()).hexdigest()) for path, text in files.items())
    return "sha256:" + hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()


class Source:
    def __init__(self, kind="skill"):
        self.kind = kind
        self.files = {"SKILL.md": "Refund instructions", "reference/policy.md": "Supporting policy"}
        self.id, self.version_id, self.name = SKILL_ID, VERSION_ID, "refund"
        if kind == "agent_context":
            link = {"mount": "skills/refund/", "skill_id": SKILL_ID, "version_id": VERSION_ID,
                    "version": 3, "digest": digest(self.files), "requested": {"version": 3}}
            self.files = {"skills/refund/" + key: value for key, value in self.files.items()}
            self.files["AGENTS.md"] = "Support agent"
            descriptor = {"schema": 1, "kind": kind, "name": "support", "description": "Support context",
                          "entrypoint": "AGENTS.md", "owned_paths": ["AGENTS.md"], "links": [link]}
            self.files[".futureagi/context.json"] = json.dumps(descriptor, sort_keys=True, separators=(",", ":"))
            self.id, self.version_id, self.name = CONTEXT_ID, CONTEXT_VERSION, "support"
        self.calls = []
        self.error = None
        self.corrupt = False
        self.requested = {"label": "production"}

    def resolve(self, *, name, selector):
        self.calls.append("resolve")
        self.requested = selector
        return {"kind": self.kind, "resource_id": self.id, "version_id": self.version_id,
                "name": self.name, "version": 3, "digest": digest(self.files), "requested": selector,
                "entrypoint": "SKILL.md" if self.kind == "skill" else "AGENTS.md",
                "descriptor_path": None if self.kind == "skill" else ".futureagi/context.json",
                "resolution_id": "synthetic-lease-never-export",
                "resolution_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "files": [{"path": path, "sha256": hashlib.sha256(text.encode()).hexdigest(), "size_bytes": len(text.encode())}
                          for path, text in sorted(self.files.items())],
                "file_count": len(self.files), "file_offset": 0, "next_file_offset": None}

    def chunk(self, identity, *, path, offset, options):
        self.calls.append(path)
        if self.error:
            raise self.error
        text = self.files[path]
        return {"resource_id": identity.resource_id, "version_id": identity.version_id, "digest": identity.digest,
                "path": path, "sha256": hashlib.sha256(text.encode()).hexdigest(), "size_bytes": len(text.encode()),
                "total_chars": len(text), "offset": offset, "next_offset": None, "eof": True,
                "text": "changed" if self.corrupt else text}


@pytest.fixture
def make_snapshot():
    from fi.context.client import SnapshotClient
    def make(kind="skill", *, tracing=True):
        source = Source(kind)
        snapshot = SnapshotClient(source, kind=kind, tracing=tracing).resolve(source.name)
        return snapshot, source
    return make


@pytest.fixture
def tracing(monkeypatch):
    pytest.importorskip("opentelemetry.sdk.trace")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from fi.telemetry import configure
    from fi.telemetry import _otel, _status
    from fi.telemetry._registry import registry
    monkeypatch.delenv("FI_SKILLS_TRACING", raising=False)
    registry._entries.clear()
    _status._logged.clear()
    _status._last_load = None
    _otel._debug_logged = False
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    configure(tracer_provider=provider)
    yield provider.get_tracer("test"), exporter, provider
    configure()
    provider.shutdown()
    registry._entries.clear()
