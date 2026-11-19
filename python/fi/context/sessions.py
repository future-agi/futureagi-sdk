"""Exact server-mapped runtime sessions over the public consumption transport.

Persist the original request and session receipt with the application's checkpoint.
Resume never resolves a label: it renews only that session's immutable lease.
This client proves authorization and byte integrity, not model delivery.
"""

from __future__ import annotations

from uuid import UUID

from fi.platform import Client, RequestOptions

from ._receipt import _attach
from .client import ContextSnapshot
from .snapshot import PAGE_SIZE, ManifestCollector, SnapshotIntegrityError
from .source import ConsumptionSource, validate_access


class ContextSessionClient:
    def __init__(self, client: Client, *, context_id: str, binding_id: str) -> None:
        self.client = client
        self.context_id = str(UUID(context_id))
        self.binding_id = str(UUID(binding_id))
        self.path = f"/model-hub/skills/contexts/bindings/{self.binding_id}/sessions/"
        self.source = ConsumptionSource(client, kind="agent_context")

    def open(self, request: dict, *, idempotency_key: str) -> dict:
        """Explicit fresh/resume operation; no retry or fallback to a fresh thread."""
        result = self.client.request("POST", self.path, body=request,
            options=RequestOptions(idempotency_key=str(UUID(idempotency_key)), max_retries=0))
        if not isinstance(result, dict):
            raise SnapshotIntegrityError("Missing server session mapping")
        expected_mode = "resumed" if request.get("resume_session_id") is not None else "fresh"
        if result.get("history_mode") != expected_mode or (
            expected_mode == "resumed" and result.get("session_id") != request["resume_session_id"]
        ):
            raise SnapshotIntegrityError("Server substituted the requested session")
        try:
            UUID(result["session_id"])
            UUID(result["resolution_id"])
        except (KeyError, ValueError, TypeError, AttributeError):
            raise SnapshotIntegrityError("Invalid server session identity") from None
        return result

    def snapshot(self, session: dict) -> ContextSnapshot:
        """Read the exact session version, preserving the server-issued lease."""
        number = session.get("version")
        if type(number) is not int or number < 1:
            raise SnapshotIntegrityError("Invalid session version")
        resolution = str(UUID(session["resolution_id"]))
        # Never follow response-provided URLs or resolve by label on resume.
        first = self.client.request("GET",
            f"/model-hub/skills/contexts/{self.context_id}/versions/{number}/manifest/",
            query={"file_offset": 0, "file_limit": PAGE_SIZE},
            options=RequestOptions(resolution_id=resolution))
        if not isinstance(first, dict) or any(first.get(key) != session.get(key)
            for key in ("version_id", "digest")) or first.get("resource_id") != self.context_id:
            raise SnapshotIntegrityError("Manifest differs from the session identity")
        collector = ManifestCollector({**first, "requested": session["requested"],
            "resolution_id": resolution,
            "resolution_expires_at": session["resolution_expires_at"]}, kind="agent_context")
        if collector.identity.version != number:
            raise SnapshotIntegrityError("Manifest differs from the session version")
        while collector.next_offset is not None:
            collector.lease.require_live()
            collector.add(self.source.manifest(collector.identity,
                offset=collector.next_offset, options=RequestOptions(resolution_id=resolution)))
        binding, session_id = self.binding_id, str(UUID(session["session_id"]))
        snapshot = ContextSnapshot(collector.finish(), self.source,
            _telemetry_binding_id=binding, _telemetry_session_id=session_id)
        self.check_access(session, snapshot)
        # The access-check uses the bound route. If mutable client metadata
        # disagrees with it, bytes remain usable but do not attest a receipt.
        if self.path == f"/model-hub/skills/contexts/bindings/{binding}/sessions/":
            _attach(snapshot, binding, session_id)
        return snapshot

    def check_access(self, session: dict, snapshot: ContextSnapshot) -> None:
        """Reauthorize before each native model boundary and context read."""
        snapshot.manifest.lease.require_live()
        if snapshot.identity.version_id != session.get("version_id") or snapshot.identity.digest != session.get("digest"):
            raise SnapshotIntegrityError("Snapshot differs from the session identity")
        result = self.client.request("POST", self.path + str(UUID(session["session_id"])) + "/access-check/", body={},
            options=RequestOptions(max_retries=0))
        validate_access(result, snapshot.identity)
        self.source.check_access(snapshot.identity, snapshot.manifest.lease)
