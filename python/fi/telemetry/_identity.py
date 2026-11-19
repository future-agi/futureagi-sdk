"""Build telemetry only from verified identity, never from bytes or lease tokens."""
from __future__ import annotations

import json
import re
from uuid import UUID


def _uuid(value):
    return str(UUID(str(value)))


def identity_attrs(identity, prefix):
    digest = identity.digest
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid digest")
    return {
        prefix + ".id": _uuid(identity.resource_id),
        prefix + ".version_id": _uuid(identity.version_id),
        prefix + ".name": identity.name.encode("utf-8")[:256].decode("utf-8", errors="ignore"),
        prefix + ".version": identity.version,
        prefix + ".digest": digest,
    }


def selector_attrs(requested, prefix="fi.skill"):
    if "label" in requested:
        return {prefix + ".requested_label": str(requested["label"])[:40]}
    if "version" in requested:
        return {prefix + ".requested_version": requested["version"]}
    return {}


def context_attrs(snapshot):
    attrs = identity_attrs(snapshot.identity, "fi.context")
    requested = snapshot.manifest.requested
    if "label" in requested:
        attrs.update(selector_attrs(requested, "fi.context"))
    from fi.context._receipt import session_receipt
    receipt = session_receipt(snapshot)
    if receipt is not None:
        attrs["fi.context.binding_id"] = receipt.binding_id
        attrs["fi.context.session_id"] = receipt.session_id
    return attrs


def verified_links(snapshot):
    """A descriptor is trusted only after VerifiedSnapshot checked its closure."""
    from fi.context.snapshot import VerifiedSnapshot
    if isinstance(snapshot, VerifiedSnapshot) and snapshot.identity.kind == "agent_context":
        return tuple(json.loads(snapshot.files[".futureagi/context.json"])["links"])
    return getattr(snapshot, "_telemetry_links", ()) or ()


def linked_attrs(snapshot, path):
    for link in verified_links(snapshot):
        if path.startswith(link["mount"]):
            from fi.context.snapshot import SnapshotIdentity
            identity = SnapshotIdentity(
                kind="skill", resource_id=link["skill_id"],
                name=link["mount"].split("/")[1], version=link["version"],
                version_id=link["version_id"], digest=link["digest"],
            )
            return identity_attrs(identity, "fi.skill"), link["requested"], path == link["mount"] + "SKILL.md"
    return None


def error_type(error):
    from fi.context.snapshot import ResolutionExpiredError, SnapshotIntegrityError
    if isinstance(error, ResolutionExpiredError):
        return "lease"
    if isinstance(error, SnapshotIntegrityError):
        return "integrity"
    code = getattr(error, "status_code", None)
    if code in (401, 403):
        return "authorization"
    if code == 404 or isinstance(error, (KeyError, FileNotFoundError)):
        return "not_found"
    return "other"
