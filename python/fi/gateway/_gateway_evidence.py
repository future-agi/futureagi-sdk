"""Request-local evidence from final HTTP headers, never from provider bodies.

Older deployments and transports without observable headers yield unknown evidence.
A dispatch attempt is not a charge: only the authoritative settlement determines
billing. Submit/poll evidence describes that request, not a later job execution.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import re
from typing import Any, Literal

DispatchState = bool | Literal["unknown"]
_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}")
_EXTENSION = "fi.gateway_evidence"


@dataclass(frozen=True)
class GatewayEvidence:
    """Immutable final-response evidence, independent of optional body mirrors.

    ``gateway_request_id`` is a validated gateway ULID; ``client_request_id`` is
    correlation only. Missing, duplicate or malformed dispatch values are unknown.
    Neither an absent header nor a provider frame proves a pre-dispatch refusal.
    """

    dispatched: DispatchState = "unknown"
    gateway_request_id: str | None = None
    client_request_id: str | None = None
    _request_id_present: bool | None = field(default=None, repr=False)


def _header_values(headers: Any, name: str) -> list[str] | None:
    """None means unobservable; an empty list means observable absence.

    HTTPX preserves raw duplicate fields. A get-only/otherwise lossy adapter is
    not evidence of a singleton or of absence. Mapping fixtures are explicit
    field inventories; combined duplicate values are rejected by the parsers.
    """
    raw = getattr(headers, "raw", None)
    if isinstance(raw, (list, tuple)):
        return [value.decode("latin-1") for key, value in raw if key.lower() == name.encode("ascii")]
    if isinstance(headers, Mapping):
        return [value for key, value in headers.items() if isinstance(key, str) and key.lower() == name]
    return None


def _single(values: list[str] | None) -> str | None:
    return values[0] if values is not None and len(values) == 1 and isinstance(values[0], str) else None


def parse_gateway_evidence(headers: Any) -> GatewayEvidence:
    """Parse only the three allowlisted evidence headers; preserve raw presence."""
    ids = _header_values(headers, "x-agentcc-request-id")
    request_id = _single(ids)
    if request_id is None or _ULID.fullmatch(request_id) is None:
        request_id = None
    raw_dispatch = _single(_header_values(headers, "x-agentcc-dispatched"))
    value = raw_dispatch.strip(" \t") if raw_dispatch is not None else None
    dispatched: DispatchState = True if value == "true" else False if value == "false" else "unknown"
    client_id = _single(_header_values(headers, "x-agentcc-client-request-id"))
    if client_id is not None and (not client_id or "," in client_id):
        client_id = None
    return GatewayEvidence(dispatched, request_id, client_id, None if ids is None else bool(ids))


def capture_gateway_evidence(response: Any) -> GatewayEvidence:
    """Capture once, before consuming the body; later headers/trailers cannot replace it."""
    extensions = getattr(response, "extensions", None)
    if isinstance(extensions, dict):
        previous = extensions.get(_EXTENSION)
        if isinstance(previous, GatewayEvidence):
            return previous
    evidence = parse_gateway_evidence(getattr(response, "headers", None))
    if isinstance(extensions, dict):
        extensions[_EXTENSION] = evidence
    return evidence


class _EvidenceDetails:
    """Descriptors reused without changing the public exception hierarchy."""

    gateway_evidence: GatewayEvidence

    @property
    def dispatched(self) -> DispatchState:
        return self.gateway_evidence.dispatched

    @property
    def gateway_request_id(self) -> str | None:
        return self.gateway_evidence.gateway_request_id

    @property
    def client_request_id(self) -> str | None:
        return self.gateway_evidence.client_request_id
