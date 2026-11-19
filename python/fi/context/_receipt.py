"""In-process telemetry provenance, not authorization or a wire credential."""
from dataclasses import dataclass, fields
from weakref import ref

from .snapshot import SnapshotIdentity


@dataclass(frozen=True, repr=False)
class _Receipt:
    # A shallow copy of an otherwise identical snapshot is not its producer.
    owner: ref
    identity: tuple
    binding_id: str
    session_id: str


def _identity(snapshot):
    identity = snapshot.identity
    return (*(getattr(identity, f.name) for f in fields(SnapshotIdentity)),
            tuple(snapshot.manifest.requested.items()))


def _attach(snapshot, binding_id, session_id):
    object.__setattr__(snapshot, '_session_origin', _Receipt(
        ref(snapshot), _identity(snapshot), binding_id, session_id))


def session_receipt(snapshot):
    receipt = getattr(snapshot, '_session_origin', None)
    if (type(receipt) is _Receipt and receipt.owner() is snapshot
            and receipt.identity == _identity(snapshot)
            and receipt.binding_id == getattr(snapshot, '_telemetry_binding_id', None)
            and receipt.session_id == getattr(snapshot, '_telemetry_session_id', None)):
        return receipt
    return None


def verified_handoff(source, result):
    receipt = session_receipt(source)
    if receipt is not None and result.manifest is source.manifest:
        object.__setattr__(result, '_telemetry_binding_id', receipt.binding_id)
        object.__setattr__(result, '_telemetry_session_id', receipt.session_id)
        _attach(result, receipt.binding_id, receipt.session_id)
    return result
